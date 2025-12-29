# CTP API Python封装安装指南

## 🎯 简短回答

**不需要搭建编译环境！** 本项目使用 `openctp-ctp` 库，这是一个预编译好的Python包，只需一行命令即可安装。

```cmd
pip install openctp-ctp
```

---

## 📦 openctp-ctp 介绍

### 什么是 openctp-ctp？

`openctp-ctp` 是OpenCTP项目提供的CTP API Python封装库：
- ✅ **预编译好的wheel包**：无需任何编译环境
- ✅ **跨平台支持**：Windows/Linux/MacOS
- ✅ **官方API兼容**：完全兼容SFIT CTP API
- ✅ **活跃维护**：版本更新及时，支持最新CTP版本
- ✅ **免费开源**：MIT许可，商业友好

### 支持的版本和平台

| 平台 | Python版本 | 架构 | 支持情况 |
|------|-----------|------|---------|
| Windows | 3.7-3.12 | x64 | ✅ 完全支持 |
| Linux | 3.7-3.12 | x64 | ✅ 完全支持 |
| MacOS | 3.7-3.12 | x64/arm64 | ✅ 完全支持 |

---

## 🚀 快速安装（推荐方法）

### Windows环境

```cmd
# 1. 打开命令提示符（CMD）或PowerShell

# 2. 安装openctp-ctp
pip install openctp-ctp

# 3. 验证安装
python -c "import openctp_ctp; print('安装成功!')"
```

### 使用国内镜像加速（可选）

如果下载速度慢，可以使用清华大学镜像：

```cmd
pip install openctp-ctp -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 📋 完整安装步骤

### 1. 检查Python版本

```cmd
python --version
```

确保Python版本在 3.7 - 3.12 之间。

### 2. 更新pip（推荐）

```cmd
python -m pip install --upgrade pip
```

### 3. 安装所有依赖

```cmd
# 进入项目目录
cd C:\path\to\whctp

# 安装全部依赖
pip install -r requirements.txt
```

或者逐个安装：

```cmd
pip install pymysql
pip install openctp-ctp
pip install pandas
```

### 4. 验证安装

```cmd
python -c "import pymysql, openctp_ctp, pandas; print('所有依赖安装成功!')"
```

---

## 🔧 进阶：如果想自己编译（不推荐）

虽然**不推荐**，但如果您想从源码编译CTP API Python封装，需要以下环境：

### Windows编译环境搭建

```cmd
# 1. 安装Visual Studio
# 下载 Visual Studio 2019/2022 Community版
# 选择"使用C++的桌面开发"工作负载

# 2. 安装SWIG
# 下载 http://www.swig.org/download.html
# 添加到系统PATH

# 3. 安装Python开发包
pip install setuptools wheel

# 4. 编译（复杂且容易出错）
# 需要CTP官方SDK头文件和库文件
# 需要编写setup.py
# 需要调试各种编译错误
```

### Linux编译环境搭建

```bash
# 1. 安装编译工具
sudo apt-get update
sudo apt-get install build-essential
sudo apt-get install python3-dev
sudo apt-get install swig

# 2. 编译（同样复杂）
# 需要处理库依赖、符号链接等问题
```

**⚠️ 警告**：自己编译非常复杂且容易出错，强烈建议直接使用 `openctp-ctp`！

---

## 🆚 方案对比

| 特性 | openctp-ctp (推荐) | 自己编译 |
|------|-------------------|---------|
| 安装难度 | ⭐ 极简单（一行命令） | ⭐⭐⭐⭐⭐ 非常复杂 |
| 环境要求 | Python即可 | 需要编译器、SWIG等 |
| 安装时间 | 1分钟 | 数小时（含踩坑） |
| 维护成本 | 低（自动更新） | 高（需手动维护） |
| 跨平台 | 完美支持 | 困难（每个平台都要配置） |
| 错误率 | 极低 | 高（编译/链接错误） |

---

## ❓ 常见问题

### Q1: 安装openctp-ctp时报错怎么办？

**A:** 尝试以下方法：

```cmd
# 方法1：使用国内镜像
pip install openctp-ctp -i https://pypi.tuna.tsinghua.edu.cn/simple

# 方法2：指定版本
pip install openctp-ctp==6.6.9

# 方法3：更新pip后重试
python -m pip install --upgrade pip
pip install openctp-ctp

# 方法4：使用虚拟环境
python -m venv venv
venv\Scripts\activate
pip install openctp-ctp
```

### Q2: 能用期货公司提供的官方SDK吗？

**A:** 可以，但需要自己封装。openctp-ctp与官方API接口兼容，所以：
- 如果用openctp-ctp开发的代码，可以无缝切换到官方SDK
- 但官方SDK是C++库，需要自己编译Python绑定

### Q3: openctp-ctp是官方的吗？

**A:** 不是官方提供的，但：
- ✅ 由OpenCTP社区维护（国内知名CTP开源社区）
- ✅ 接口与官方CTP完全兼容
- ✅ 在生产环境广泛使用
- ✅ GitHub上1000+ stars，可靠性高

### Q4: 没有网络怎么办？

**A:** 可以离线安装：

```cmd
# 在有网络的机器上下载wheel文件
pip download openctp-ctp -d ./packages

# 拷贝packages文件夹到目标机器，然后安装
pip install --no-index --find-links=./packages openctp-ctp
```

### Q5: 本项目能在没有openctp-ctp的情况下运行吗？

**A:** 可以！本项目有自动降级机制：
- 如果检测到openctp-ctp已安装 → 使用真实CTP连接
- 如果未安装 → 自动切换到模拟模式
- 所有功能（GUI、数据库）都能正常使用

查看 [ctp_api_real.py](ctp_api_real.py) 第8-15行：

```python
try:
    from openctp_ctp import tdapi, mdapi
    CTP_AVAILABLE = True
except ImportError:
    print("警告: openctp-ctp未安装，将使用模拟模式")
    CTP_AVAILABLE = False
```

---

## 📚 参考资源

- **OpenCTP官网**: https://openctp.cn/
- **openctp-ctp GitHub**: https://github.com/openctp/openctp-ctp-python
- **PyPI页面**: https://pypi.org/project/openctp-ctp/
- **CTP API文档**: api/doc/《SFIT-CTP-MINI-API接口开发文档》.pdf
- **OpenCTP文档**: https://openctp.github.io/docs/

---

## 🎉 总结

**结论：不需要搭建编译环境！**

使用 `openctp-ctp` 库只需一行命令：

```cmd
pip install openctp-ctp
```

就这么简单！享受Python开发的便利，无需折腾编译环境。

如有任何问题，欢迎查看项目文档或OpenCTP社区。
