from networkx import graph_edit_distance
import networkx as nx
from torch.utils.data import DataLoader
import os
import dgl
import torch as th
import matplotlib.pyplot as plt
import re

class UnsupportedInstanceError(Exception):
    pass
class HeteroGraph:
    """
        输入: sp_netlist 或 json 格式的电路数据，解析其中的组件信息，并完成3种等价表示的补全。
        主要方法: 
            - generate_all_from_spectre_netlist: 输入 spectre netlist, 输出json和graph
            - generate_all_from_json: 输入 json, 输出spectre netlist和graph
    
    """
    def __init__(self):
        # 初始化命令
        self.num_pmos = 0
        self.edge_dp2n = []
        self.edge_gp2n = []
        self.edge_sp2n = []
        self.edge_bp2n = []
        self.pmos_name = {}
        self.pmos_feature = []

        self.num_nmos = 0
        self.edge_dn2n = []
        self.edge_gn2n = []
        self.edge_sn2n = []
        self.edge_bn2n = []
        self.nmos_name = {}
        self.nmos_feature = []

        self.num_pnp = 0
        self.edge_bpnp2n = []
        self.edge_epnp2n = []
        self.edge_cpnp2n = []
        self.pnp_name = {}
        self.pnp_feature = []

        self.num_npn = 0
        self.edge_bnpn2n = []
        self.edge_enpn2n = []
        self.edge_cnpn2n = []
        self.npn_name = {}
        self.npn_feature = []

        self.num_r = 0
        self.edge_r2n = []
        self.r_name = {}
        self.r_feature = []

        self.num_c = 0
        self.edge_c2n = []
        self.c_name = {}
        self.c_feature = []

        self.num_l = 0
        self.edge_l2n = []
        self.l_name = {}
        self.l_feature = []

        self.num_s = 0
        self.edge_s2n = []
        self.s_name = {}
        self.s_feature = []

        self.num_diode = 0
        self.edge_diode_p2n = []
        self.edge_diode_n2n = []
        self.diode_name = {}
        self.diode_feature = []
        
        self.num_isource = 0
        self.edge_iin2n = []
        self.edge_iout2n = []
        self.isource_name = {}
        self.isource_feature = []

        self.num_vsource = 0
        self.edge_vp2n = []
        self.edge_vn2n = []
        self.vsource_name = {}
        self.vsource_feature = []

        self.num_diso = 0
        self.edge_diso_vp2n = []
        self.edge_diso_vn2n = []
        self.edge_diso_vout2n = []
        self.diso_name = {}
        self.diso_feature = []

        self.num_dido = 0
        self.edge_dido_vp2n = []
        self.edge_dido_vn2n = []
        self.edge_dido_voutp2n = []
        self.edge_dido_voutn2n = []
        self.dido_name = {}
        self.dido_feature = []

        self.num_siso = 0
        self.edge_siso_vin2n = []
        self.edge_siso_vout2n = []
        self.siso_name = {}
        self.siso_feature = []

        self.num_net = 0
        self.net_name = {}

        self.type_mapping = {
            'PMOS': 'pmos',
            'NMOS': 'nmos',
            'NPN': 'npn',
            'PNP': 'pnp',
            'Res': 'resistor',
            'Cap': 'capacitor',
            'Ind': 'inductor',
            'Diode': 'diode',
            'Switch': 'switch',
            'Current': 'isource',
            'Voltage': 'vsource',
            'Diso_amp': 'diffamp',
            'Siso_amp': 'amp',
            'Dido_amp': 'dido'
        }

        self.json = {}
        self.json_netlist = []
        self.label = ''
        self.sp_netlist = ''
        self.het_graph = None 
        self.skip_json = False


    def set_label(self,label):
        self.label = label

    def set_sp_netlist(self,sp_netlist):
        self.sp_netlist = sp_netlist

    def set_json(self,json):
        self.json = json
        self.json_netlist = json['ckt_netlist']
        self.label = json['ckt_type']

    def extract_col(self,matrix):
        # 提取第一列和第二列
        src = [row[0] for row in matrix]
        dst = [row[1] for row in matrix]
        return src, dst

    def extract_content(self,text):
        # 定义正则表达式模式
        pattern = re.compile(r'[A-Z][a-zA-Z0-9]* \(')
        
        # 找到所有匹配的行
        matches = list(pattern.finditer(text))
        
        if not matches:
            return "没有找到符合格式的内容"
        
        # 获取第一个和最后一个匹配的位置
        first_pos = matches[0].start()
        last_pos = matches[-1].start()
        
        # 找到最后一个匹配行的结束位置
        last_line_end = text.find('\n', last_pos)
        if last_line_end == -1:
            last_line_end = len(text)
        
        # 提取第一个和最后一个匹配之间的内容
        extracted_content = text[first_pos:last_line_end]

        return extracted_content 

    def get_component_info(self,line):
        match_1 = re.match(r'(\w+)\s*\(([^)]+)\)', line)
        if not match_1:
                return False
        # 提取第一个单词
        name = match_1.group(1)

        # 提取括号中的内容，并分割成列表
        ports = match_1.group(2).split()
        
        # 查找第一个捕获组
        match_2 = re.search(r'\)\s+(\w+)', line)
        type = match_2.group(1)

        # 从第一个捕获组开始的子字符串
        start_index = match_2.end(1)
        substring = line[start_index:]

        # 正则表达式匹配 <变量名>=<值>
        pattern = re.compile(r'(\w+)=([^,\s]+)')
        matches = pattern.findall(substring)

        # 将匹配结果保存到字典中
        values = {var: val for var, val in matches}
        
        return name, ports, type, values

    def reset_globals(self):
        self.num_pmos = 0
        self.edge_dp2n = []
        self.edge_gp2n = []
        self.edge_sp2n = []
        self.edge_bp2n = []
        self.pmos_name = {}
        self.pmos_feature = []

        self.num_nmos = 0
        self.edge_dn2n = []
        self.edge_gn2n = []
        self.edge_sn2n = []
        self.edge_bn2n = []
        self.nmos_name = {}
        self.nmos_feature = []

        self.num_pnp = 0
        self.edge_bpnp2n = []
        self.edge_epnp2n = []
        self.edge_cpnp2n = []
        self.pnp_name = {}
        self.pnp_feature = []

        self.num_npn = 0
        self.edge_bnpn2n = []
        self.edge_enpn2n = []
        self.edge_cnpn2n = []
        self.npn_name = {}
        self.npn_feature = []

        self.num_r = 0
        self.edge_r2n = []
        self.r_name = {}
        self.r_feature = []

        self.num_c = 0
        self.edge_c2n = []
        self.c_name = {}
        self.c_feature = []

        self.num_l = 0
        self.edge_l2n = []
        self.l_name = {}
        self.l_feature = []

        self.num_s = 0
        self.edge_s2n = []
        self.s_name = {}
        self.s_feature = []

        self.num_diode = 0
        self.edge_diode_p2n = []
        self.edge_diode_n2n = []
        self.diode_name = {}
        self.diode_feature = []
        
        self.num_isource = 0
        self.edge_iin2n = []
        self.edge_iout2n = []
        self.isource_name = {}
        self.isource_feature = []

        self.num_vsource = 0
        self.edge_vp2n = []
        self.edge_vn2n = []
        self.vsource_name = {}
        self.vsource_feature = []

        self.num_diso = 0
        self.edge_diso_vp2n = []
        self.edge_diso_vn2n = []
        self.edge_diso_vout2n = []
        self.diso_name = {}
        self.diso_feature = []

        self.num_dido = 0
        self.edge_dido_vp2n = []
        self.edge_dido_vn2n = []
        self.edge_dido_voutp2n = []
        self.edge_dido_voutn2n = []
        self.dido_name = {}
        self.dido_feature = []

        self.num_siso = 0
        self.edge_siso_vin2n = []
        self.edge_siso_vout2n = []
        self.siso_name = {}
        self.siso_feature = []

        self.num_net = 0
        self.net_name = {}

        
    def get_key_from_value(self,dict,value):
        reversed_dict = {v: k for k, v in dict.items()}
        key = reversed_dict.get(value)
        return key

    def plot_het(self,nx_g1):
        
        import matplotlib.pyplot as plt
        import networkx as nx
        import matplotlib.patches as mpatches

        color_map = {
        'PNP': '#2ECC71',  # 绿色，稍微亮一些
        'NPN': '#9B59B6',  # 紫色，稍微亮一些
        'R': '#FAD02E',    # 橙色，保持不变
        'C': '#007E6D',    # 青色，保持不变
        'L': '#FF5733',    # 亮红色，新的颜色
        'ISOURCE': '#F39C12',  # 深黄色，新的颜色
        'VSOURCE': '#FF69B4',  # 粉色，稍微亮一些
        'DISO': '#A52A2A',  # 棕色，保持不变
        'DIDO': '#95A5A6',  # 灰色，稍微亮一些
        'SISO': '#34495E',  # 深蓝色，替代黑色
        'net': '#6C30A2',   # 深紫色，保持不变
        'PMOS': '#0043AC',  # 蓝色，保持不变
        'NMOS': '#D82D5B',   # 红色，保持不变
        "DIODE": "#FFD700",
        "S": "#8B4513",
    }

        # 获取节点类型并为每个节点分配颜色
        node_colors = []
        for n, d in nx_g1.nodes(data=True):
            ntype = d['ntype']
            node_colors.append(color_map[ntype])

        # 绘制图形
        plt.figure(figsize=(12, 12))
        pos = nx.spring_layout(nx_g1)
        nx.draw_networkx_nodes(nx_g1, pos, alpha=1, node_size=150, node_color=node_colors)
        ax = plt.gca()
        for e in nx_g1.edges:
            ax.annotate("",
                        xy=pos[e[0]], xycoords='data',
                        xytext=pos[e[1]], textcoords='data',
                        arrowprops=dict(arrowstyle="-", color="0",
                                        linewidth=2,  
                                        shrinkA=10, shrinkB=10,
                                        patchA=None, patchB=None,
                                        connectionstyle="arc3,rad=rrr".replace('rrr', str(0.3*e[2]))
                                        ),
                        )

        # 添加图例
        legend_handles = [mpatches.Patch(color=color, label=label) for label, color in color_map.items()]
        plt.legend(handles=legend_handles, loc='best')
        # 关闭坐标轴
        plt.axis('off')
        # 显示图像
        plt.show()

    def get_net_index(self,ports,is_3=False):
        net_index = []
        if is_3:
            for net in ports[:3]:
                if net not in self.net_name:
                    self.net_name[net] = self.num_net
                    self.num_net = self.num_net + 1
                net_index.append(self.net_name[net])
        else:
            for net in ports:
                if net not in self.net_name:
                    self.net_name[net] = self.num_net
                    self.num_net = self.num_net + 1
                net_index.append(self.net_name[net])
        return net_index


    def create_pmos(self,component_info):

        name, ports, type, values = component_info
        self.pmos_name[name] = self.num_pmos
        self.num_pmos = self.num_pmos + 1
        net_index = self.get_net_index(ports,True)
        self.edge_dp2n.append([self.pmos_name[name], net_index[0]])
        self.edge_gp2n.append([self.pmos_name[name], net_index[1]])
        self.edge_sp2n.append([self.pmos_name[name], net_index[2]])
        #self.edge_bp2n.append([self.pmos_name[name], net_index[3]])

        if self.skip_json:
            return
        port_0 = self.get_key_from_value(self.net_name,net_index[0])
        port_1 = self.get_key_from_value(self.net_name,net_index[1])
        port_2 = self.get_key_from_value(self.net_name,net_index[2])
        #port_3 = self.get_key_from_value(self.net_name,net_index[3])
        
        component_dict = {
            'component_type': 'PMOS',
            'port_connection': {'Drain': port_0, 'Gate': port_1, 'Source':port_2, },}
        self.json_netlist.append(component_dict)
        return
    def create_pmos4(self,component_info):

        name, ports, type, values = component_info
        self.pmos_name[name] = self.num_pmos
        self.num_pmos = self.num_pmos + 1
        net_index = self.get_net_index(ports)
        self.edge_dp2n.append([self.pmos_name[name], net_index[0]])
        self.edge_gp2n.append([self.pmos_name[name], net_index[1]])
        self.edge_sp2n.append([self.pmos_name[name], net_index[2]])
        self.edge_bp2n.append([self.pmos_name[name], net_index[3]])

        if self.skip_json:
            return
        port_0 = self.get_key_from_value(self.net_name,net_index[0])
        port_1 = self.get_key_from_value(self.net_name,net_index[1])
        port_2 = self.get_key_from_value(self.net_name,net_index[2])
        port_3 = self.get_key_from_value(self.net_name,net_index[3])
        
        component_dict = {
            'component_type': 'PMOS',
            'port_connection': {'Drain': port_0, 'Gate': port_1, 'Source':port_2, 'Body':port_3},}
        self.json_netlist.append(component_dict)
        return
    def create_nmos(self, component_info):
        name, ports, type, values = component_info
        self.nmos_name[name] = self.num_nmos
        self.num_nmos += 1
        net_index = self.get_net_index(ports,True)
        self.edge_dn2n.append([self.nmos_name[name], net_index[0]])
        self.edge_gn2n.append([self.nmos_name[name], net_index[1]])
        self.edge_sn2n.append([self.nmos_name[name], net_index[2]])
        #self.edge_bn2n.append([self.nmos_name[name], net_index[3]])
        
        if self.skip_json:
            return
        
        port_0 = self.get_key_from_value(self.net_name, net_index[0])
        port_1 = self.get_key_from_value(self.net_name, net_index[1])
        port_2 = self.get_key_from_value(self.net_name, net_index[2])
        #port_3 = self.get_key_from_value(self.net_name, net_index[3])
        
        component_dict = {
            'component_type': 'NMOS',
            'port_connection': {'Drain': port_0, 'Gate': port_1, 'Source': port_2,},}
        
        self.json_netlist.append(component_dict)

        return
    
    def create_nmos4(self, component_info):
        name, ports, type, values = component_info
        self.nmos_name[name] = self.num_nmos
        self.num_nmos += 1
        net_index = self.get_net_index(ports)
        self.edge_dn2n.append([self.nmos_name[name], net_index[0]])
        self.edge_gn2n.append([self.nmos_name[name], net_index[1]])
        self.edge_sn2n.append([self.nmos_name[name], net_index[2]])
        self.edge_bn2n.append([self.nmos_name[name], net_index[3]])
        
        if self.skip_json:
            return
        
        port_0 = self.get_key_from_value(self.net_name, net_index[0])
        port_1 = self.get_key_from_value(self.net_name, net_index[1])
        port_2 = self.get_key_from_value(self.net_name, net_index[2])
        port_3 = self.get_key_from_value(self.net_name, net_index[3])
        
        component_dict = {
            'component_type': 'NMOS',
            'port_connection': {'Drain': port_0, 'Gate': port_1, 'Source': port_2, 'Body': port_3},}
        
        self.json_netlist.append(component_dict)

        return
    def create_pnp(self, component_info):
        name, ports, type, values = component_info
        self.pnp_name[name] = self.num_pnp
        self.num_pnp += 1
        net_index = self.get_net_index(ports,is_3=True)
        self.edge_cpnp2n.append([self.pnp_name[name], net_index[0]])
        self.edge_bpnp2n.append([self.pnp_name[name], net_index[1]])
        self.edge_epnp2n.append([self.pnp_name[name], net_index[2]])
        
        if self.skip_json:
            return
        port_collector = self.get_key_from_value(self.net_name, net_index[0])
        port_base = self.get_key_from_value(self.net_name, net_index[1])
        port_emitter = self.get_key_from_value(self.net_name, net_index[2])

        component_dict = {
            'component_type': 'PNP',
            'port_connection': {'Collector': port_collector, 'Base': port_base, 'Emitter': port_emitter},}
        
        self.json_netlist.append(component_dict)

        return
    def create_npn(self, component_info):
        name, ports, type, values = component_info
        self.npn_name[name] = self.num_npn
        self.num_npn += 1
        net_index = self.get_net_index(ports,is_3=True)
        self.edge_cnpn2n.append([self.npn_name[name], net_index[0]])
        self.edge_bnpn2n.append([self.npn_name[name], net_index[1]])
        self.edge_enpn2n.append([self.npn_name[name], net_index[2]])
        
        if self.skip_json:
            return
        port_collector = self.get_key_from_value(self.net_name, net_index[0])
        port_base = self.get_key_from_value(self.net_name, net_index[1])
        port_emitter = self.get_key_from_value(self.net_name, net_index[2])

        component_dict = {
            'component_type': 'NPN',
            'port_connection': {'Collector': port_collector, 'Base': port_base, 'Emitter': port_emitter},}
        
        self.json_netlist.append(component_dict)

        return
    def create_resistor(self, component_info):
        name, ports, type, values = component_info
        self.r_name[name] = self.num_r
        self.num_r += 1
        net_index = self.get_net_index(ports)
        self.edge_r2n.append([self.r_name[name], net_index[0]])
        self.edge_r2n.append([self.r_name[name], net_index[1]])
        
        if self.skip_json:
            return
        port_pos = self.get_key_from_value(self.net_name, net_index[0])
        port_neg = self.get_key_from_value(self.net_name, net_index[1])

        component_dict = {
            'component_type': 'Res',
            'port_connection': {'Pos': port_pos, 'Neg': port_neg},}
        
        self.json_netlist.append(component_dict)

        return
    def create_capacitor(self, component_info):
        name, ports, type, values = component_info
        self.c_name[name] = self.num_c
        self.num_c += 1
        net_index = self.get_net_index(ports)
        self.edge_c2n.append([self.c_name[name], net_index[0]])
        self.edge_c2n.append([self.c_name[name], net_index[1]])
        
        if self.skip_json:
            return
        port_pos = self.get_key_from_value(self.net_name, net_index[0])
        port_neg = self.get_key_from_value(self.net_name, net_index[1])

        component_dict = {
            'component_type': 'Cap',
            'port_connection': {'Pos': port_pos, 'Neg': port_neg},}
        
        self.json_netlist.append(component_dict)

        return
    def create_inductor(self, component_info):
        name, ports, type, values = component_info
        self.l_name[name] = self.num_l
        self.num_l += 1
        net_index = self.get_net_index(ports)
        self.edge_l2n.append([self.l_name[name], net_index[0]])
        self.edge_l2n.append([self.l_name[name], net_index[1]])
        
        if self.skip_json:
            return
        port_pos = self.get_key_from_value(self.net_name, net_index[0])
        port_neg = self.get_key_from_value(self.net_name, net_index[1])

        component_dict = {
            'component_type': 'Ind',
            'port_connection': {'Pos': port_pos, 'Neg': port_neg},}
        
        self.json_netlist.append(component_dict)

        return
    def create_switch(self, component_info):
        name, ports, type, values = component_info
        self.s_name[name] = self.num_s
        self.num_s += 1
        net_index = self.get_net_index(ports)
        self.edge_s2n.append([self.s_name[name], net_index[0]])
        self.edge_s2n.append([self.s_name[name], net_index[1]])
        
        if self.skip_json:
            return
        port_pos = self.get_key_from_value(self.net_name, net_index[0])
        port_neg = self.get_key_from_value(self.net_name, net_index[1])

        component_dict = {
            'component_type': 'Switch',
            'port_connection': {'Pos': port_pos, 'Neg': port_neg},}
        
        self.json_netlist.append(component_dict)

        return

    def create_diode(self, component_info):
        name, ports, type, values = component_info
        self.diode_name[name] = self.num_diode
        self.num_diode += 1
        net_index = self.get_net_index(ports)
        self.edge_diode_p2n.append([self.diode_name[name], net_index[0]])
        self.edge_diode_n2n.append([self.diode_name[name], net_index[1]])
        
        if self.skip_json:
            return
        port_in = self.get_key_from_value(self.net_name, net_index[0])
        port_out = self.get_key_from_value(self.net_name, net_index[1])

        component_dict = {
            'component_type': 'Diode',
            'port_connection': {'In': port_in, 'Out': port_out},}
        
        self.json_netlist.append(component_dict)

        return

    def create_isource(self, component_info):
        name, ports, type, values = component_info
        self.isource_name[name] = self.num_isource
        self.num_isource += 1
        net_index = self.get_net_index(ports)
        self.edge_iin2n.append([self.isource_name[name], net_index[0]])
        self.edge_iout2n.append([self.isource_name[name], net_index[1]])
        
        if self.skip_json:
            return
        port_in = self.get_key_from_value(self.net_name, net_index[0])
        port_out = self.get_key_from_value(self.net_name, net_index[1])

        component_dict = {
            'component_type': 'Current',
            'port_connection': {'In': port_in, 'Out': port_out},}
        
        self.json_netlist.append(component_dict)

        return

    def create_vsource(self, component_info):
        name, ports, type, values = component_info
        self.vsource_name[name] = self.num_vsource
        self.num_vsource += 1
        net_index = self.get_net_index(ports)
        self.edge_vp2n.append([self.vsource_name[name], net_index[0]])
        self.edge_vn2n.append([self.vsource_name[name], net_index[1]])
        
        if self.skip_json:
            return
        port_positive = self.get_key_from_value(self.net_name, net_index[0])
        port_negative = self.get_key_from_value(self.net_name, net_index[1])

        component_dict = {
            'component_type': 'Voltage',
            'port_connection': {'Positive': port_positive, 'Negative': port_negative},}
        
        self.json_netlist.append(component_dict)

        return
    def create_diso(self, component_info):
        name, ports, type, values = component_info
        self.diso_name[name] = self.num_diso
        self.num_diso += 1
        net_index = self.get_net_index(ports)
        self.edge_diso_vp2n.append([self.diso_name[name], net_index[0]])
        self.edge_diso_vn2n.append([self.diso_name[name], net_index[1]])
        self.edge_diso_vout2n.append([self.diso_name[name], net_index[2]])
        
        if self.skip_json:
            return
        port_inp = self.get_key_from_value(self.net_name, net_index[0])
        port_inn = self.get_key_from_value(self.net_name, net_index[1])
        port_out = self.get_key_from_value(self.net_name, net_index[2])

        component_dict = {
            'component_type': 'Diso_amp',
            'port_connection': {'InP': port_inp, 'InN': port_inn, 'Out': port_out},}
        
        self.json_netlist.append(component_dict)

        return
    def create_dido(self, component_info):
        name, ports, type, values = component_info
        self.dido_name[name] = self.num_dido
        self.num_dido += 1
        net_index = self.get_net_index(ports)
        self.edge_dido_vp2n.append([self.dido_name[name], net_index[0]])
        self.edge_dido_vn2n.append([self.dido_name[name], net_index[1]])
        self.edge_dido_voutp2n.append([self.dido_name[name], net_index[2]])
        self.edge_dido_voutn2n.append([self.dido_name[name], net_index[3]])
        
        if self.skip_json:
            return
        port_inp = self.get_key_from_value(self.net_name, net_index[0])
        port_inn = self.get_key_from_value(self.net_name, net_index[1])
        port_outp = self.get_key_from_value(self.net_name, net_index[2])
        port_outn = self.get_key_from_value(self.net_name, net_index[3])

        component_dict = {
            'component_type': 'Dido_amp',
            'port_connection': {'InP': port_inp, 'InN': port_inn, 'OutP': port_outp, 'OutN': port_outn},}
        
        self.json_netlist.append(component_dict)

        return
    def create_siso(self, component_info):
        name, ports, type, values = component_info
        self.siso_name[name] = self.num_siso
        self.num_siso += 1
        net_index = self.get_net_index(ports)
        self.edge_siso_vin2n.append([self.siso_name[name], net_index[0]])
        self.edge_siso_vout2n.append([self.siso_name[name], net_index[1]])
        
        if self.skip_json:
            return
        port_in = self.get_key_from_value(self.net_name, net_index[0])
        port_out = self.get_key_from_value(self.net_name, net_index[1])

        component_dict = {
            'component_type': 'Siso_amp',
            'port_connection': {'In': port_in, 'Out': port_out},}
        
        self.json_netlist.append(component_dict)

        return

    def generate_all_from_spectre_netlist(self,label,sp_netlist,is_json_generated = False):
        self.set_label(label)
        self.set_sp_netlist(sp_netlist)
        self.reset_globals()
        self.skip_json = is_json_generated

        is_successful = True
        data = self.extract_content(sp_netlist)

        for line in data.strip().split('\n'):  # 处理每行
            component_info = self.get_component_info(line)
            if not component_info:
                continue
            try:
                # 设置索引序号, 创建边
                match component_info[2]:
                    case 'pmos': 
                        self.create_pmos(component_info)
                    case 'pmos4':
                        self.create_pmos4(component_info)
                    case 'nmos':
                        self.create_nmos(component_info)
                    case 'nmos4':
                        self.create_nmos4(component_info)
                    case 'npn':
                        self.create_npn(component_info)
                    case 'pnp':
                        self.create_pnp(component_info)
                    case 'resistor' | 'res':
                        self.create_resistor(component_info)
                    case 'capacitor' | 'cap':
                        self.create_capacitor(component_info)
                    case 'inductor':
                        self.create_inductor(component_info)
                    case 'diode':
                        self.create_diode(component_info)
                    case 'switch':
                        self.create_switch(component_info)
                    case 'isource':
                        self.create_isource(component_info)
                    case 'vsource':
                        self.create_vsource(component_info)
                    case 'amp':
                        self.create_siso(component_info)
                    case 'diffamp' | 'opamp':
                        self.create_diso(component_info)
                    case 'dido'|'fullydiffamp':
                        self.create_dido(component_info)
                    case _:
                        
                        print(f"unsupported instance occurs")
                        print(component_info)
                        raise UnsupportedInstanceError("Unsupported instance type encountered")
            except UnsupportedInstanceError as e:
                print(f"Error: {e}")
                is_successful = False
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                is_successful = False
        graph_data = {
            ('PMOS', 'dp2n', 'net'): (
                th.tensor(self.extract_col(self.edge_dp2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_dp2n)[1], dtype=th.int64)),
            
            ('PMOS', 'gp2n', 'net'): (
                th.tensor(self.extract_col(self.edge_gp2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_gp2n)[1], dtype=th.int64)),
            ('PMOS', 'sp2n', 'net'): (
                th.tensor(self.extract_col(self.edge_sp2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_sp2n)[1], dtype=th.int64)),
            ('PMOS', 'bp2n', 'net'): (
                th.tensor(self.extract_col(self.edge_bp2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_bp2n)[1], dtype=th.int64)),
            ('NMOS', 'dn2n', 'net'): (
                th.tensor(self.extract_col(self.edge_dn2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_dn2n)[1], dtype=th.int64)),
            ('NMOS', 'gn2n', 'net'): (
                th.tensor(self.extract_col(self.edge_gn2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_gn2n)[1], dtype=th.int64)),
            ('NMOS', 'sn2n', 'net'): (
                th.tensor(self.extract_col(self.edge_sn2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_sn2n)[1], dtype=th.int64)),
            ('NMOS', 'bn2n', 'net'): (
                th.tensor(self.extract_col(self.edge_bn2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_bn2n)[1], dtype=th.int64)),
            ('PNP', 'cpnp2n', 'net'): (
                th.tensor(self.extract_col(self.edge_cpnp2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_cpnp2n)[1], dtype=th.int64)),
            ('PNP', 'bpnp2n', 'net'): (
                th.tensor(self.extract_col(self.edge_bpnp2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_bpnp2n)[1], dtype=th.int64)),
            ('PNP', 'epnp2n', 'net'): (
                th.tensor(self.extract_col(self.edge_epnp2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_epnp2n)[1], dtype=th.int64)),
            ('NPN', 'cnpn2n', 'net'): (
                th.tensor(self.extract_col(self.edge_cnpn2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_cnpn2n)[1], dtype=th.int64)),
            ('NPN', 'bnpn2n', 'net'): (
                th.tensor(self.extract_col(self.edge_bnpn2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_bnpn2n)[1], dtype=th.int64)),
            ('NPN', 'enpn2n', 'net'): (
                th.tensor(self.extract_col(self.edge_enpn2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_enpn2n)[1], dtype=th.int64)),
            ('R', 'r2n', 'net'): (
                th.tensor(self.extract_col(self.edge_r2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_r2n)[1], dtype=th.int64)),
            ('C', 'c2n', 'net'): (
                th.tensor(self.extract_col(self.edge_c2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_c2n)[1], dtype=th.int64)),
            ('L', 'l2n', 'net'): (
                th.tensor(self.extract_col(self.edge_l2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_l2n)[1], dtype=th.int64)),
            ('S', 's2n', 'net'): (
                th.tensor(self.extract_col(self.edge_s2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_s2n)[1], dtype=th.int64)),
            ('DIODE', 'diode_p2n', 'net'): (
                th.tensor(self.extract_col(self.edge_diode_p2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_diode_p2n)[1], dtype=th.int64)),
            ('DIODE', 'diode_n2n', 'net'): (
                th.tensor(self.extract_col(self.edge_diode_n2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_diode_n2n)[1], dtype=th.int64)),
            ('ISOURCE', 'iin2n', 'net'): (
                th.tensor(self.extract_col(self.edge_iin2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_iin2n)[1], dtype=th.int64)),
            ('ISOURCE', 'iout2n', 'net'): (
                th.tensor(self.extract_col(self.edge_iout2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_iout2n)[1], dtype=th.int64)),
            ('VSOURCE', 'vp2n', 'net'): (
                th.tensor(self.extract_col(self.edge_vp2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_vp2n)[1], dtype=th.int64)),
            ('VSOURCE', 'vn2n', 'net'): (
                th.tensor(self.extract_col(self.edge_vn2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_vn2n)[1], dtype=th.int64)),
            ('DISO', 'diso_vp2n', 'net'): (
                th.tensor(self.extract_col(self.edge_diso_vp2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_diso_vp2n)[1], dtype=th.int64)),
            ('DISO', 'diso_vn2n', 'net'): (
                th.tensor(self.extract_col(self.edge_diso_vn2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_diso_vn2n)[1], dtype=th.int64)),
            ('DISO', 'diso_vout2n', 'net'): (
                th.tensor(self.extract_col(self.edge_diso_vout2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_diso_vout2n)[1], dtype=th.int64)),
            ('DIDO', 'dido_vp2n', 'net'): (
                th.tensor(self.extract_col(self.edge_dido_vp2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_dido_vp2n)[1], dtype=th.int64)),
            ('DIDO', 'dido_vn2n', 'net'): (
                th.tensor(self.extract_col(self.edge_dido_vn2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_dido_vn2n)[1], dtype=th.int64)),
            ('DIDO', 'dido_voutp2n', 'net'): (
                th.tensor(self.extract_col(self.edge_dido_voutp2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_dido_voutp2n)[1], dtype=th.int64)),
            ('DIDO', 'dido_voutn2n', 'net'): (
                th.tensor(self.extract_col(self.edge_dido_voutn2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_dido_voutn2n)[1], dtype=th.int64)),
            ('SISO', 'siso_vin2n', 'net'): (
                th.tensor(self.extract_col(self.edge_siso_vin2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_siso_vin2n)[1], dtype=th.int64)),
            ('SISO', 'siso_vout2n', 'net'): (
                th.tensor(self.extract_col(self.edge_siso_vout2n)[0], dtype=th.int64),
                th.tensor(self.extract_col(self.edge_siso_vout2n)[1], dtype=th.int64))
        }
        self.het_graph = None
        self.het_graph = dgl.heterograph(graph_data) # 没有设置特征值，仅设置定义了连接关系。
        self.reset_globals()

        if not is_json_generated:
            self.json = {}
            self.json['ckt_type'] = self.label
            self.json['ckt_netlist'] = self.json_netlist
            self.json_netlist = []
            print('json netlist cleared.')
        
        return self.json,self.het_graph, is_successful

    def generate_spectre_netlist_from_json(self):

        netlist_lines = []
        
        for component in self.json_netlist:
            component_type = component.get('component_type')
            port_connection = component.get('port_connection', {})

            if not component_type or not port_connection:
                continue  # Skip invalid components
            
            # Map the component type to the corresponding Spectre type
            spectre_type = self.type_mapping.get(component_type)
            if (spectre_type == 'pmos' or spectre_type == 'nmos') and len(port_connection) == 4:
                spectre_type = 'pmos4' if spectre_type == 'pmos' else 'nmos4'

            if not spectre_type:
                continue  # Skip if the component type is not recognized

            # Generate the netlist line for the given component
            ports = ' '.join(port_connection.values())
            netlist_line = f"X1 ({ports}) {spectre_type}"
            netlist_lines.append(netlist_line)
        # Join all netlist lines into a single string
        
        netlist_str = '\n'.join(netlist_lines)
        self.sp_netlist = netlist_str
        return 

    def generate_all_from_json(self,json):
        self.set_json(json)
        self.generate_spectre_netlist_from_json()
        _,_,is_successful = self.generate_all_from_spectre_netlist(self.label,self.sp_netlist,is_json_generated=True)
        return self.sp_netlist, self.het_graph,is_successful



## utils

def to_MG(nx_g):
    # 创建一个多重图
    MG = nx.MultiGraph()
    # 添加节点并赋予属性
    for node, data in nx_g.nodes(data=True):
        MG.add_node(node, ntype=data['ntype'])
    # 添加多条边并赋予属性
    for u, v, key, data in nx_g.edges(keys=True, data=True):
        MG.add_edge(u, v, key=key, etype=str(data['etype'][1]))
    return MG

def node_match(dicta,dictb):
    if dicta['ntype'] == dictb['ntype']:
        return True
    else:
        return False
def edge_match(dicta,dictb):
    if dicta['etype'] == dictb['etype']:
        return True
    else:
        return False
    
def ged(graph1, graph2):
    # 计算graph1和graph2的图编辑距离

    nx_1 = to_MG(graph1.to_networkx().to_undirected())
    nx_2 = to_MG(graph2.to_networkx().to_undirected())
    return graph_edit_distance(nx_1,nx_2,node_match,edge_match,timeout=1)

def minimum(lst):
    if not lst:
        raise ValueError("列表不能为空")
    
    minimum = lst[0]
    for num in lst[1:]:
        if num < minimum:
            minimum = num
    return minimum
def average(lst):
    # 检查列表是否为空
    if not lst:
        raise ValueError("列表不能为空")
    
    # 初始化总和和计数器
    total_sum = 0
    count = 0
    
    # 遍历列表，累加总和并计数
    for num in lst:
        total_sum += num
        count += 1
    
    # 计算平均数
    average = total_sum / count
    return average

def load_from_pkl(pkl_path):
    import pickle
    with open(pkl_path, 'rb') as f:
        return pickle.load(f)
    print(f'test cases are loaded from {pkl_path}')