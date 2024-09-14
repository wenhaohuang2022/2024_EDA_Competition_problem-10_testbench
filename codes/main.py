import time
import warnings
import os
from math import log10  
from utils import *

# 单个测例的测试函数
def test_case(case, solution,timeout=30):
    # 获取测例信息：编号、电路图、电路功能、spectre网表和异构图
    case_id = case['case_id'] 
    true_label = case['label'] 
    true_graph = case['graph'] 
    case_image = case['image'] 

    print(f'开始测试测例 {case_id}')

    # 开始计时
    start_time = time.time() 
    # 运行参数队伍的算法，输入电路图，输出由电路功能和网表组成的字典
    result = solution(case_image)
    # 停止计时
    end_time = time.time() 
    # 计算运行时间
    elapsed_time = end_time - start_time 

    # 获取待测的电路功能
    ckt_label = result['ckt_type']
    # 检测电路功能是否判断正确
    test1_result = 1 if ckt_label == true_label else 0
    
    # 获取待测的电路连接
    raw = HeteroGraph()
    # 将字典形式的网表转化为等价的异构图
    _,ckt_graph,_ = raw.generate_all_from_json(result)
    # 多次计算GED，取最小值
    test2_results = []
    test2_result_min = None
    N = 3 # 重复计算3次
    for i in range(0,N):
        ged_result = ged(ckt_graph, true_graph,timeout)
        if ged_result == 0:
            test2_result_min = 0
            break
        test2_results.append(ged_result)
        if i == N-1:
            test2_result_min = minimum(test2_results)
    
    # 生成单个测例的测试报告
    report = {'测例编号':case_id,'功能识别精确度F':test1_result,'网表识别精确度K':test2_result_min,'运行时间T':elapsed_time}
    return report

# 格式化输出测试报告
def generate_report(reports,F_total,K_total,T_total,num_cases):
    # 按照测例编号，将结果从小到大排序
    def extract_case_number(report):
        id = report['测例编号']
        return int(id.split('_')[1])
    reports.sort(key=extract_case_number)

    # 将运行时间以微秒表示
    reports_T_in_ns = reports 
    for report in reports_T_in_ns:
        report['运行时间T'] = report['运行时间T'] * 1000000 
        report["运行时间T (us)"] = report.pop("运行时间T")
    

    # 设置表头
    headers = ["测例编号", "功能识别精确度F", "网表识别精确度K", "运行时间T (us)"]

    # 创建表头行和分隔行
    header_line = " | ".join(headers)
    separator_line = " | ".join(["---"] * len(headers))

    # 创建数据行
    rows = []
    for report in reports_T_in_ns:
        row = []
        for header in headers:
            if header == "运行时间T (us)":
                value = float(report[header])
                formatted_value = f"{value:.1f}"
                row.append(formatted_value)
            else:
                row.append(str(report[header]))
        rows.append(" | ".join(row))

    # 计算最终结果并保存
    final_F = F_total / num_cases
    final_K = 1 / log10(10 + K_total)
    final_T = T_total * 1000000 / num_cases
    final_result = f"\n ## 综合测试结果\n\n总得分| 功能识别精确度F | 网表识别精确度K | 平均运行时间T (us)\n--- | --- | --- | --- \n 略 | {final_F:.1f} | {final_K:.1f} | {final_T:.3f} \n\n"
    markdown_table = f"# 测试报告\n\n{header_line}\n{separator_line}\n" + "\n".join(rows) + final_result
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'report_on_public_cases.md')
    with open(report_path, "w", encoding="utf-8") as file:
        file.write(markdown_table)
    print(f"测试报告已保存在 {report_path}")

# 运行所有测例的函数
def run_tests(solution,timeout=30):

    # 初始化测试结果
    reports = []
    K_total = 0
    F_total = 0
    T_total = 0

    # 加载所有的测试用例
    pkl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'public.pkl')
    public_cases = load_from_pkl(pkl_path)
    num_cases = len(public_cases)   

    # 开始测试
    for case in public_cases:

        ##############测试部分###################
        
        report = test_case(case, solution,timeout)
        
        ########################################

        print(f'测例 {report["测例编号"]} 已完成')

        # 获取单个测试结果
        K_total += report['网表识别精确度K']
        F_total += report['功能识别精确度F']
        T_total += report['运行时间T']
        reports.append(report)

    # 格式化并输出测试结果
    generate_report(reports,F_total,K_total,T_total,num_cases)
    


if __name__ == '__main__':
    # 忽略警告信息
    warnings.filterwarnings("ignore", category=FutureWarning)
    
    # 导入参赛队伍的解决方案
    from my_solution import solution
    # 运行测试
    run_tests(solution,timeout=1)

    







    
    

    
    
