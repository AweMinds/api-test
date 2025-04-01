import requests, datetime, sys
import pandas as pd
import os


def get_tenant_access_token():
    """
    获取租户访问令牌。
    返回:
        str: 访问令牌。
    """
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    # 准备请求数据，包含应用的ID和密钥
    headers = {"Content-Type": "application/json; charset=utf-8"}
    post_data = {"app_id": "cli_a760e38bc64cd01c", "app_secret": "lRVMaU0CGiZLU4oEmSORUc0GUYsVKBgx"}
    # 向飞书接口发送POST请求，获取访问令牌
    r = requests.post(url, json=post_data, headers=headers)
    response = r.json()
    
    if r.status_code != 200 or response.get("code") != 0:
        error_msg = response.get("msg", "未知错误")
        raise Exception(f"获取tenant_access_token失败: {error_msg}")
    
    # 从响应中提取租户访问令牌和过期时间
    access_token = response["tenant_access_token"]
    expire = response["expire"]
    
    return access_token


def get_sheet_id(spreadsheet_token, access_token=None):
    """
    根据电子表格token获取表格中所有工作表及其ID。
    
    参数:
        spreadsheet_token (str): 电子表格的token。
        access_token (str, optional): 访问令牌。默认为None，会自动调用get_tenant_access_token()获取。
    
    返回:
        dict: 工作表标题到工作表ID的映射。
    """
    if access_token is None:
        access_token = get_tenant_access_token()
    
    url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{spreadsheet_token}/sheets/query"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.text}")
        return {}
    
    data = response.json()
    
    if data.get("code") != 0:
        print(f"Error: {data.get('code')}, {data.get('msg')}")
        return {}
    
    sheets = data.get("data", {}).get("sheets", [])
    
    # 创建工作表标题到工作表ID的映射
    sheet_map = {sheet["title"]: sheet["sheet_id"] for sheet in sheets}
    
    return sheet_map


def read_data(spreadsheet_token, sheet_id=None, sheet_name=None, access_token=None):
    """
    根据电子表格的token和sheet_id或sheet_name读取数据。
    
    参数:
        spreadsheet_token (str): 电子表格的token。
        sheet_id (str, optional): 工作表的ID。如果提供了sheet_name，可以为None。
        sheet_name (str, optional): 工作表的名称。如果提供了sheet_id，可以为None。
        access_token (str, optional): 访问令牌。默认为None，会自动调用get_tenant_access_token()获取。
    
    返回:
        pd.DataFrame: 包含工作表数据的DataFrame。
    """
    if access_token is None:
        access_token = get_tenant_access_token()
    
    # 如果提供了sheet_name但没有提供sheet_id，则获取sheet_id
    if sheet_id is None and sheet_name is not None:
        sheet_map = get_sheet_id(spreadsheet_token, access_token)
        if sheet_name not in sheet_map:
            print(f"Error: Sheet '{sheet_name}' not found in the spreadsheet.")
            return pd.DataFrame()
        sheet_id = sheet_map[sheet_name]
    
    if sheet_id is None:
        print("Error: Either sheet_id or sheet_name must be provided.")
        return pd.DataFrame()
    
    # 1. 先获取工作表信息，检查工作表类型和属性
    url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{spreadsheet_token}/sheets/{sheet_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.text}")
        return pd.DataFrame()
    
    sheet_info = response.json()
    
    if sheet_info.get("code") != 0:
        print(f"Error: {sheet_info.get('code')}, {sheet_info.get('msg')}")
        return pd.DataFrame()
    
    sheet_data = sheet_info.get("data", {}).get("sheet", {})
    
    # 2. 检查工作表类型是否为"sheet"，只有电子表格类型才能读取数据
    if sheet_data.get("resource_type") != "sheet":
        print(f"Cannot read data: The sheet type is {sheet_data.get('resource_type')}, not a regular spreadsheet.")
        return pd.DataFrame()
    
    # 3. 获取工作表数据
    url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values/{sheet_id}"
    params = {
        'valueRenderOption': 'ToString',
        'dateTimeRenderOption': 'FormattedString'
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.text}")
        return pd.DataFrame()
    
    data = response.json()
    
    # 提取表格数据
    values = data.get('data', {}).get('valueRange', {}).get('values', [])
    
    # 将数据转换为DataFrame
    if values:
        if len(values) > 0:
            df = pd.DataFrame(values[1:], columns=values[0])  # 第一行作为列名
            return df
        else:
            print("No data found in the specified range.")
            return pd.DataFrame()
    else:
        print("No data returned from the API.")
        return pd.DataFrame()


def add_data(spreadsheet_token, sheet_id=None, sheet_name=None, column="A", value="", access_token=None, insert_data_option="OVERWRITE"):
    """
    向指定工作表的指定列最末端单元格添加数据。
    
    参数:
        spreadsheet_token (str): 电子表格的token。
        sheet_id (str, optional): 工作表的ID。如果提供了sheet_name，可以为None。
        sheet_name (str, optional): 工作表的名称。如果提供了sheet_id，可以为None。
        column (str): 要添加数据的列，如 "A", "B" 等，默认为 "A"。
        value (str): 要添加的单元格数据。
        access_token (str, optional): 访问令牌。默认为None，会自动调用get_tenant_access_token()获取。
        insert_data_option (str, optional): 追加数据的方式, 默认为 "INSERT_ROWS"。
                                          可选值为 "OVERWRITE" 或 "INSERT_ROWS"。
    
    返回:
        dict: API响应数据。
    """
    if access_token is None:
        access_token = get_tenant_access_token()
    
    # 如果提供了sheet_name但没有提供sheet_id，则获取sheet_id
    if sheet_id is None and sheet_name is not None:
        sheet_map = get_sheet_id(spreadsheet_token, access_token)
        if sheet_name not in sheet_map:
            print(f"Error: Sheet '{sheet_name}' not found in the spreadsheet.")
            return {}
        sheet_id = sheet_map[sheet_name]
    
    if sheet_id is None:
        print("Error: Either sheet_id or sheet_name must be provided.")
        return {}
    
    # 构建API请求URL - 使用values_append端点
    url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values_append"
    
    # 构建请求头
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    # 构建请求参数
    params = {
        "insertDataOption": insert_data_option
    }
    
    # 构建请求体
    # 使用 "sheet_id!A:A" 这种格式，表示在A列找到第一个空白位置添加数据
    range_value = f"{sheet_id}!{column}:{column}"
    data = {
        "valueRange": {
            "range": range_value,
            "values": [[value]]  # 使用二维数组，因为API需要这种格式
        }
    }
    
    # 发送POST请求
    response = requests.post(url, headers=headers, params=params, json=data)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.text}")
        return {}
    
    result = response.json()
    
    if result.get("code") != 0:
        print(f"Error: {result.get('code')}, {result.get('msg')}")
        return {}
    
    return result.get("data", {})





# def read_data_by_sheet_id(spreadsheet_id, range, access_token=None):
#     """
#     根据Sheet ID和范围读取数据。
#     参数:
#         spreadsheet_id (str): 表格ID。
#         range (str): 数据范围。
#         access_token (str, optional): 访问令牌。默认为None，会自动调用get_tenant_access_token()获取。
#     返回:
#         pd.DataFrame: 数据DataFrame。
#     """
#     if access_token is None:
#         access_token = get_tenant_access_token()
        
#     url = f"https://open.feishu.cn/open-apis/sheet/v2/spreadsheets/{spreadsheet_id}/values/{range}"
#     headers = {"Authorization": f"Bearer {access_token}",
#                "Content-Type": "application/json; charset=utf-8",
#                }
#     params = {
#         'valueRenderOption': 'ToString',
#         'dateTimeRenderOption': 'FormattedString'
#     }
#     response = requests.get(url, headers=headers, params=params)
#     if response.status_code == 200:
#         data = response.json()
#         # 提取表格数据
#         values = data.get('data', {}).get('valueRange', {}).get('values', [])

#         # 将数据转换为 DataFrame
#         if values:
#             df = pd.DataFrame(values[1:], columns=values[0])  # 第一行作为列名
#             return df
#         else:
#             print("No data found in the specified range.")
#             return None
#     else:
#         print(f"Error: {response.status_code}, {response.text}")
#         return pd.DataFrame()

# def sheet_msg_query(spreadsheet_id, access_token=None):
#     """
#     查询Sheet信息。
#     参数:
#         spreadsheet_id (str): 表格ID。
#         access_token (str, optional): 访问令牌。默认为None，会自动调用get_tenant_access_token()获取。
#     返回:
#         pd.DataFrame: 包含Sheet信息的DataFrame。
#     """
#     if access_token is None:
#         access_token = get_tenant_access_token()
        
#     url = f'https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{spreadsheet_id}/sheets/query'
#     headers = {"Authorization": f"Bearer {access_token}",
#                "Content-Type": "application/json; charset=utf-8",
#                }
#     response = requests.get(url, headers=headers)
#     if response.status_code == 200:
#         data = response.json()
#         # 提取表格数据
#         sheets = data.get('data', {}).get('sheets', [])
#         sheet_ids = [sheet['sheet_id'] for sheet in sheets]
#         sheet_titles = [sheet['title'] for sheet in sheets]
#         df = pd.DataFrame({'sheet_id': sheet_ids, 'sheet_name': sheet_titles})
#         return df
#     else:
#         print(f"Error: {response.status_code}, {response.text}")
#         return pd.DataFrame()


# def read_data_by_sheet_name(spreadsheet_id, sheet_name, access_token=None):
#     """
#     根据Sheet名称读取数据。
#     参数:
#         spreadsheet_id (str): 表格ID。
#         sheet_name (str): Sheet名称。
#         access_token (str, optional): 访问令牌。默认为None，会自动调用get_tenant_access_token()获取。
#     返回:
#         pd.DataFrame: 数据DataFrame。
#     """
#     if access_token is None:
#         access_token = get_tenant_access_token()
        
#     sheet_msg_df = sheet_msg_query(spreadsheet_id, access_token)
#     sheet_id = sheet_msg_df[sheet_msg_df['sheet_name']==sheet_name]['sheet_id'].values[0]
#     df = read_data_by_sheet_id(spreadsheet_id=spreadsheet_id, range=sheet_id, access_token=access_token)
#     return df
    
# if __name__ == "__main__":
#     # 用法示例
#     # 查询Sheet信息
#     sheet_msg_df = sheet_msg_query(spreadsheet_id='xxx')

#     # 读取指定Sheet名称的数据
#     df = read_data_by_sheet_name(spreadsheet_id='xxx', sheet_name='20240101基础信息')