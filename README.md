# README

本文介绍了2024年EDA精英挑战赛赛题十《针对模拟电路的电路图到网表自动生成》的测试平台使用方法。参赛队伍可以选择（1）在服务器上运行测试代码，也可以选择（2）将本文件夹中的测试文件下载到本地，完成本地环境的配置，并按照下述的使用方法完成测试。

## 文件说明

- codes文件夹
  - main.py：执行测试的主程序，参赛队伍**需要拷贝或下载**此文件；
  - my_solution.py：参赛队伍的解决方案，**需由参赛队伍编写**；
  - utils.py：工具函数库，仅由main.py调用，参赛队伍无需修改本文件，**但是要和main.py一起拷贝或下载**；
  - public.pkl文件：公开测试样例的二进制文件，由main.py调用，**需要拷贝或下载**；
  - 提示：应确保**需要拷贝或下载**的文件都和**my_solution.py**存放在同一文件夹下。
- public文件夹：存放公开测试样例，供参赛队伍参考，无需下载；
- log.log：测试平台更新的日志文件，无需下载；
- README.md：测试平台使用说明，无需下载。

## 环境依赖

服务器上的运行环境已为大家配置好了，若选择（1）在服务器上运行代码，只需在运行时选择Python3.8.10 64-bit (路径为/bin/python3)的python解释器即可，并将codes文件夹中需要拷贝的文件拷贝到用户自己的文件夹中；若选择（2）在本地完成测试，则需要自行完成环境配置：

```plaintext
python 3.8+
networkx 3.1
numpy 1.24.4
torch 2.4.0
pydantic 2.9.1
pandas 2.0.3
dgl 2.4.0
```

并在本地新建一个文件夹，将codes中需要下载的文件存放到该文件夹中。

## 使用方法

参赛队伍需将解决方案封装成一个名为**solution的函数（函数名不可修改）**，并在**my_solution.py**中定义。my_solution.py的一个示例如下（网表中，网络的名称不会对结果有任何影响，可以是'net1'，'vdd'，'1'，也可以是'#$dfsgklx!*&^'）：

```python
# import ...

# 示例solution函数（仅用于说明）
def solution(case_image):
    # 读入一张电路图
    image = case_image 

    # case_image是二进制图像编码，可通过下面的方式转存为png格式
    # 假设输出图像文件路径为case_image_path
    case_image_path = 'case_image.png'
    with open(case_image_path, 'wb') as img_file:
        img_file.write(image)
    # 当不需要输出图像文件时，可以注释掉这段的代码


  
    # 经过一系列算法处理，得到电路功能和网表

    # ......
    # ......
    # ......

    # 假设得到的结果为：(这里用的是case_4的例子)
    ckt_type = 'DIDO-Amplifier'
    ckt_netlist = [{'component_type': 'NMOS',
                  'port_connection': {'Drain': 'voutp',
                                      'Gate': 'vin',
                                      'Source': 'net1'}},
                 {'component_type': 'NMOS',
                  'port_connection': {'Drain': 'voutn',
                                      'Gate': 'vip',
                                      'Source': 'net1'}},
                 {'component_type': 'PMOS',
                  'port_connection': {'Drain': 'voutp',
                                      'Gate': 'vcmfb',
                                      'Source': 'vdd!'}},
                 {'component_type': 'PMOS',
                  'port_connection': {'Drain': 'voutn',
                                      'Gate': 'vcmfb',
                                      'Source': 'vdd!'}},
                 {'component_type': 'Current',
                  'port_connection': {'In': 'net1', 'Out': '0'}}]
    return {'ckt_type':ckt_type, 'ckt_netlist':ckt_netlist}
```

运行**main.py**, 即可开始测试。也可以在命令行模式下直接运行main.py文件：

```shell
cd /your/directory/path # 转换到存放测试文件的文件夹下
python3 main.py
```

**main.py**将对参赛队伍的solution函数进行测试（如下方代码所示），并生成一个名为**report_on_public_cases.md**的测试报告文件，存放在当前文件夹中。如需了解更多测试过程的细节，请参阅**main.py**文件。

```python
if __name__ == '__main__':
    # 忽略警告信息
    warnings.filterwarnings("ignore", category=FutureWarning)
  
    # 导入参赛队伍的解决方案
    from my_solution import solution
    # 运行测试
    run_tests(solution) 
```

打开**report_on_public_cases.md**文件，可以查看测试报告。报告列出了20个测例的测试结果以及综合测试结果。关于功能识别精确度F、网表识别精确度K和运行时间的定义和计算方法，详见[赛题指南](https://edaoss.icisc.cn/file/cacheFile/2024/8/7/20bb61c66e7246b48c3bef32f5f2378b.pdf)。

下面是一个测试报告的样例。在这个例子中，solution函数每次均输出case_4的电路功能和网表，故可以看到只有case_4的网表识别精确度K等于0，而其他测例得到的K都不为零，且K越大表明solution的输出与标准结果相差越远。

```markdown
# 测试报告

| 测例编号 | 功能识别精确度F | 网表识别精确度K | 运行时间T (us) |
| -------- | --------------- | --------------- | -------------- |
| case_1   | 0               | 48.0            | 354.1          |
| case_2   | 0               | 32.0            | 160.9          |
| case_3   | 0               | 40.0            | 252.0          |
| case_4   | 1               | 0               | 216.0          |
| case_5   | 0               | 95.0            | 270.6          |
| case_6   | 0               | 109.0           | 251.5          |
| case_7   | 0               | 37.0            | 307.3          |
| case_8   | 1               | 19.0            | 315.2          |
| case_9   | 0               | 25.0            | 256.1          |
| case_10  | 0               | 77.0            | 376.7          |
| case_11  | 0               | 48.0            | 290.6          |
| case_12  | 0               | 72.0            | 381.9          |
| case_13  | 0               | 133.0           | 393.2          |
| case_14  | 0               | 29.0            | 209.1          |
| case_15  | 0               | 15.0            | 248.7          |
| case_16  | 0               | 16.0            | 329.5          |
| case_17  | 0               | 53.0            | 300.9          |
| case_18  | 0               | 132.0           | 318.5          |
| case_19  | 0               | 76.0            | 230.1          |
| case_20  | 0               | 41.0            | 248.7          |
 ## 综合测试结果

| 总得分 | 功能识别精确度F | 网表识别精确度K | 平均运行时间T (us) |
| ------ | --------------- | --------------- | ------------------ |
| 略     | 0.1             | 0.3             | 285.578            |
```

由于目前各支队伍正处于作品准备阶段，我们对上述三个参数的计算方法略作调整：对于功能识别精确度$F$和运行时间$T$，综合结果为20个测例各自结果的平均值；对于网表识别精确度$K$，综合结果由公式 $\frac{1}{lg(10+\sum_{i=1}^{20}K_i)}$ 算得。

每个$K_i$的计算方法如下：重复执行3次$GED$计算，每次$GED$的运行时间上限设为30秒（为提高测试效率，参赛队伍可根据自己的测试情况自行修改时间上限，但是最终赛题评审阶段的时间上限仍和赛题指南中保持一致）；如果遇到$GED$为0，则立刻返回；若达到迭代最大次数，将返回最小的$GED$值。由于总得分的计算依赖于所有队伍的最终测试结果，故在报告中省略。

$GED$运行时间的修改方法：在main.py文件末尾运行测试的部分，添加参数timeout并赋值即可：

```python
if __name__ == '__main__':
    # 忽略警告信息
    warnings.filterwarnings("ignore", category=FutureWarning)
  
    # 导入参赛队伍的解决方案
    from my_solution import solution
    # 运行测试
    run_tests(solution,timeout=10) # 修改GED计算时间上限为10s
```

 最后，**public文件夹**内存放了公开测试样例的电路图图片**image.png**、字典形式的网表**netlist_dict.txt**和spectre网表**netlist_spectre.txt**，供大家参考。

 祝大家参赛愉快！加油！！

 更新日期：2024年9月14日
