import os
import pickle
from utils import HeteroGraph,UnsupportedInstanceError
import ast

def read_dict_from_file(file_path):
    # 读取文件内容
    with open(file_path, 'r') as file:
        dict_str = file.read()
    # 使用 ast.literal_eval 将字符串转换为字典
    dictionary = ast.literal_eval(dict_str)
    return dictionary


def process_case_folder(folder_path):
    json_netlist_path = os.path.join(folder_path, 'netlist_dict.txt')    
    json_netlist = read_dict_from_file(json_netlist_path)

    label = json_netlist['ckt_type']
    sp_netlist_path = os.path.join(folder_path, 'netlist_spectre.txt')
    with open(sp_netlist_path, 'r') as file:
        sp_netlist = file.read()

    image_path = os.path.join(folder_path, 'image.png')
    with open(image_path, 'rb') as img_file:
        img_data = img_file.read()
    

    raw = HeteroGraph()
    json_netlist,graph,is_successful = raw.generate_all_from_spectre_netlist(label,sp_netlist,False)

    case = {
        'case_id': os.path.basename(folder_path),
        'label': label,
        'image': img_data,
        'netlist_spectre': sp_netlist,
        'netlist_dict': json_netlist,
        'graph': graph,
    }

    if not is_successful:
        print(f'case {case['case_id']} is NOT successfully processed\n')
    else:
        print(f'case {case['case_id']} is successfully processed\n')
    return case  

def generate_test_cases(root_folder):
    test_cases = []
    for folder_name in os.listdir(root_folder):
        folder_path = os.path.join(root_folder, folder_name)
        if os.path.isdir(folder_path):
            case = process_case_folder(folder_path)
            test_cases.append(case)
    return test_cases


def save_to_pkl(test_cases,pkl_relative_path):
    import pickle
    with open(pkl_relative_path, 'wb') as f:
        pickle.dump(test_cases, f)
    print(f'test cases are saved to {pkl_relative_path}')









if __name__ == '__main__':
    # 运行本文件以生成测试用例，只需要修改两处路径：

    # folder_path 修改为测试用例的源文件夹路径 （绝对路径）
    folder_path = '/home/huangwenhao/WORK/gnn_project/EDA_comp/public'


    # pkl_relative_path 修改为测试用例的存储路径（相对路径）
    pkl_path = '/home/huangwenhao/WORK/gnn_project/EDA_comp/public/public.pkl'

    public_cases = generate_test_cases(folder_path)
    save_to_pkl(public_cases,pkl_path)




    
