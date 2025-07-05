import sys
import os
import json
import time

# Add the parent directory to sys.path to import the LLM module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LLM.openai_based_api import process_content

def load_agent_tools():
    """加载Agent工具定义"""
    try:
        tools_file = os.path.join(os.path.dirname(__file__), 'Agent_Tools.json')
        with open(tools_file, 'r', encoding='utf-8') as f:
            tools_data = json.load(f)
        return tools_data['tools']
    except Exception as e:
        print(f"Error loading agent tools: {e}")
        return None

def mock_tool_function(tool_name, arguments):
    """模拟工具函数的执行结果"""
    print(f"\n🔧 模拟执行工具: {tool_name}")
    print(f"📋 参数: {json.dumps(arguments, ensure_ascii=False, indent=2)}")
    
    # 根据不同的工具返回不同的模拟结果
    if tool_name == "full_text_search":
        return {
            "results": [
                {"title": "文档1", "content": f"这是关于'{arguments.get('query', '')}'的全文搜索结果示例", "score": 0.95},
                {"title": "文档2", "content": f"另一个包含'{arguments.get('query', '')}'的文档内容", "score": 0.87}
            ],
            "total": 2
        }
    elif tool_name == "keyword_search":
        keywords = arguments.get('keywords', [])
        return {
            "results": [
                {"title": "关键词文档1", "content": f"这是包含关键词{keywords}的精确匹配结果", "score": 1.0},
                {"title": "关键词文档2", "content": f"另一个匹配{keywords}的文档", "score": 0.92}
            ],
            "total": 2
        }
    elif tool_name == "vector_search":
        return {
            "results": [
                {"title": "语义文档1", "content": f"这是与'{arguments.get('query', '')}'语义相关的内容", "similarity": 0.89},
                {"title": "语义文档2", "content": f"另一个语义相似的文档内容", "similarity": 0.82}
            ],
            "total": 2
        }
    else:
        return {"error": f"Unknown tool: {tool_name}"}

def simulate_conversation_with_tools(provider_name, model, system_prompt, user_query, tools, max_rounds=3):
    """模拟带有工具调用的对话"""
    print(f"\n{'='*80}")
    print(f"🤖 开始Agent对话模拟")
    print(f"📝 用户查询: {user_query}")
    print(f"{'='*80}")
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_query})
    
    for round_num in range(max_rounds):
        print(f"\n--- 第 {round_num + 1} 轮对话 ---")
        
        # 调用LLM
        response = process_content(
            provider_name=provider_name,
            user_prompt=user_query if round_num == 0 else "",
            model=model,
            system_prompt=system_prompt if round_num == 0 else None,
            tools=tools,
            tool_choice="auto"
        )
        
        print(f"💬 模型响应: {response['result']}")
        
        # 检查是否有工具调用
        if 'tool_calls' in response and response['tool_calls']:
            print(f"\n🛠️  检测到 {len(response['tool_calls'])} 个工具调用")
            
            # 处理每个工具调用
            tool_messages = []
            for tool_call in response['tool_calls']:
                tool_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}
                
                # 模拟工具执行
                tool_result = mock_tool_function(tool_name, arguments)
                print(f"✅ 工具结果: {json.dumps(tool_result, ensure_ascii=False, indent=2)}")
                
                # 添加工具消息到对话历史
                tool_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False)
                })
            
            # 如果有工具调用，继续对话让模型处理工具结果
            if tool_messages:
                # 构建包含工具调用历史的消息
                messages.append({
                    "role": "assistant", 
                    "content": response['result'],
                    "tool_calls": response['tool_calls']
                })
                messages.extend(tool_messages)
                
                # 让模型处理工具结果
                follow_up_response = process_content(
                    provider_name=provider_name,
                    user_prompt="",  # 空查询，让模型基于工具结果继续
                    model=model,
                    tools=tools
                )
                
                print(f"\n🎯 基于工具结果的最终回答: {follow_up_response['result']}")
                break
        else:
            print("\n✨ 对话完成，无需工具调用")
            break
    
    print(f"\n{'='*80}")
    return response

def run_agent_tests():
    """运行Agent测试套件"""
    # 配置
    provider_name = "YUNWU-Dev"
    model = "gpt-4.1-2025-04-14"
    
    # 加载工具定义
    tools = load_agent_tools()
    if not tools:
        print("❌ 无法加载工具定义，退出测试")
        return
    
    print(f"✅ 成功加载 {len(tools)} 个工具:")
    for tool in tools:
        print(f"   - {tool['function']['name']}: {tool['function']['description']}")
    
    # 系统提示词
    system_prompt = """# Identity
You are an AI assistant, developed by AweMinds Technology Co., Ltd. 
Your primary role is to help customers by answering questions about content in the knowledge base which you can fully access by tool calls. 

# Instructions
## goals
Answer the user's request using the relevant tool(s), if they are available. Check that all the required parameters for each tool call are provided or can reasonably be inferred from context. IF there are no relevant tools or there are missing values for required parameters, ask the user to supply these values; otherwise proceed with the tool calls. If the user provides a specific value for a parameter (for example provided in quotes), make sure to use that value EXACTLY. DO NOT make up values for or ask about optional parameters. Carefully analyze descriptive terms in the request as they may indicate required parameter values that should be included even if not explicitly quoted.

## tool_calling
You have tools at your disposal to solve the user's query. Follow these rules regarding tool calls:
1. ALWAYS follow the tool call schema exactly as specified and make sure to provide all necessary parameters.
2. The conversation may reference tools that are no longer available. NEVER call tools that are not explicitly provided.
3. NEVER refer to tool names when speaking to the USER. Instead, just say what the tool is doing in natural language.
4. After receiving tool results, carefully reflect on their quality and determine optimal next steps before proceeding. Use your thinking to plan and iterate based on this new information, and then take the best next action. Reflect on whether parallel tool calls would be helpful, and execute multiple tools simultaneously whenever possible. Avoid slow sequential tool calls when not necessary.
5. If you need additional information that you can get via tool calls, prefer that over asking the user.
6. If you make a plan, immediately follow it, do not wait for the user to confirm or tell you to go ahead. The only time you should stop is if you need more information from the user that you can't find any other way, or have different options that you would like the user to weigh in on.
7. The vast majority of tools provided to you support multi-parameter combinations, such as vector searches using 5 or more keywords/phrases. If you wish to attempt multi-angle searches by providing multiple sets of parameters to obtain more comprehensive results, this is encouraged.

## maximize_parallel_tool_calls
CRITICAL: Execute multiple tool calls simultaneously whenever possible for maximum efficiency.
**When to use parallel calls:**
- Multiple searches with different keywords/methods
- Gathering information from various sources
- Any operations that don't depend on each other's output
**Process:**
1. Plan all needed information upfront
2. Execute all relevant tools together
3. Only use sequential calls when one tool's output is required for the next tool's input
**Default behavior:** Parallel execution unless operations are genuinely interdependent.

## search_and_reading
If you are unsure about the answer to the USER's request or how to satisfy their request, you should gather more information. This can be done with additional tool calls, asking clarifying questions, etc...
For example, if you've performed a semantic search, and the results may not fully answer the USER's request, or warrant additional research, feel free to call more tools.
If you've performed an answer that may partially satisfy the USER's query, but you're not confident, gather more information or use more tools before ending your turn.
Bias towards not asking the user for help if you can find the answer yourself."""

    # 复杂测试用例 - 评估RAG系统在复杂场景下的表现
    test_cases = [
        {
            "name": "身份测试",
            "query": "你能干什么？",
            "expected_tools": []
        },
        {
            "name": "复杂因果链推理",
            "query": "如果公司A在2020年收购了公司B，而公司B之前在2018年与公司C签署了独家供应协议，那么在2021年公司A推出新产品时，这个独家供应协议对其市场策略会产生什么影响？请分析至少三个层面的连锁反应。",
            "expected_tools": ["full_text_search", "keyword_search", "vector_search"]
        },
        {
            "name": "多源数据矛盾处理",
            "query": "文档A显示某药物的临床试验成功率为78%，文档B显示为65%，文档C显示为82%。请分析这些数据差异的可能原因，并判断哪个数据更可信，同时解释你的判断依据。",
            "expected_tools": ["full_text_search", "keyword_search"]
        },
        {
            "name": "时间序列因果分析",
            "query": "某公司股价在发布财报前一周开始上涨，财报发布当天继续上涨，但第二天开始下跌。同期，该公司的主要竞争对手发布了新产品。请分析这一系列事件的内在逻辑关系和可能的市场预期变化。",
            "expected_tools": ["full_text_search", "vector_search"]
        },
        {
            "name": "概念边界模糊问题",
            "query": "在人工智能领域，'机器学习'、'深度学习'和'神经网络'这三个概念经常被混用。请在特定语境下（比如某篇论文或某个产品介绍中）准确区分它们的含义，并解释为什么在该语境下这种区分是重要的。",
            "expected_tools": ["vector_search", "keyword_search"]
        },
        {
            "name": "复合计算验证",
            "query": "某公司声称其新算法比现有方案效率提升了300%，同时能耗降低了40%，成本减少了60%。请根据相关技术文档验证这些数据的一致性和可信度，并分析是否存在逻辑矛盾。",
            "expected_tools": ["full_text_search", "keyword_search"]
        },
        {
            "name": "跨学科综合分析",
            "query": "量子计算的发展对现有的RSA加密算法构成威胁，这种威胁对金融行业的区块链应用会产生什么影响？请从技术、法律、经济三个角度进行综合分析。",
            "expected_tools": ["full_text_search", "keyword_search", "vector_search"]
        },
        {
            "name": "隐含关系推导",
            "query": "如果张三是ABC公司的CTO，李四是XYZ基金的合伙人，而王五曾在DEF咨询公司工作过，现在他们三人共同出现在一份关于区块链项目的投资协议中。请推断这个项目可能的技术特点、资金规模和市场定位。",
            "expected_tools": ["vector_search", "full_text_search"]
        },
        {
            "name": "假设情景推演",
            "query": "假设某项新技术使得电池能量密度提高了10倍，请分析这一突破对电动汽车产业链、能源结构、城市规划可能产生的连锁影响，并评估各种影响发生的时间顺序和概率。",
            "expected_tools": ["vector_search", "full_text_search", "keyword_search"]
        },
        {
            "name": "纯逻辑推理测试",
            "query": "如果事件A发生的概率是70%，在A发生的条件下B发生的概率是80%，在B发生的条件下C发生的概率是60%。现在已知C发生了，请计算A发生的概率，并解释你的推理过程。",
            "expected_tools": []
        }
    ]
    
    # 执行测试
    total_tests = len(test_cases)
    passed_tests = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'#'*100}")
        print(f"🧪 测试用例 {i}/{total_tests}: {test_case['name']}")
        print(f"{'#'*100}")
        
        try:
            start_time = time.time()
            response = simulate_conversation_with_tools(
                provider_name=provider_name,
                model=model,
                system_prompt=system_prompt,
                user_query=test_case['query'],
                tools=tools
            )
            end_time = time.time()
            
            # 分析结果
            has_tool_calls = 'tool_calls' in response and response['tool_calls']
            used_tools = []
            if has_tool_calls:
                used_tools = [call.function.name for call in response['tool_calls']]
            
            print(f"\n📊 测试结果分析:")
            print(f"   ⏱️  耗时: {end_time - start_time:.2f} 秒")
            print(f"   🔧 使用的工具: {used_tools}")
            print(f"   🎯 期望的工具: {test_case['expected_tools']}")
            print(f"   📊 输入token: {response.get('input_tokens', 0)}")
            print(f"   📤 输出token: {response.get('output_tokens', 0)}")
            
            # 简单的测试验证
            if not test_case['expected_tools']:
                # 期望无工具调用
                if not has_tool_calls:
                    print("   ✅ 测试通过: 正确地没有使用工具")
                    passed_tests += 1
                else:
                    print("   ❌ 测试失败: 不应该使用工具但却使用了")
            else:
                # 期望有工具调用
                if has_tool_calls:
                    # 检查是否使用了期望的工具
                    expected_set = set(test_case['expected_tools'])
                    used_set = set(used_tools)
                    if used_set.intersection(expected_set):
                        print("   ✅ 测试通过: 使用了期望的工具")
                        passed_tests += 1
                    else:
                        print("   ⚠️  测试部分通过: 使用了工具但不是期望的工具")
                        passed_tests += 0.5
                else:
                    print("   ❌ 测试失败: 应该使用工具但没有使用")
                    
        except Exception as e:
            print(f"   ❌ 测试异常: {e}")
    
    # 总结
    print(f"\n{'='*100}")
    print(f"🏆 测试总结")
    print(f"{'='*100}")
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"通过率: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("🎉 所有测试都通过了！")
    elif passed_tests >= total_tests * 0.8:
        print("👍 大部分测试通过，Agent表现良好")
    else:
        print("⚠️  需要改进Agent的工具调用逻辑")

def main():
    """主函数"""
    print("🚀 Agent Function Call 测试开始")
    print("=" * 50)
    
    try:
        run_agent_tests()
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 Agent测试完成")

if __name__ == "__main__":
    main()
