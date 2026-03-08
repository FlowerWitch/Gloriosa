# DarkLink Scanner

暗链扫描工具

## 安装
```bash
pip install -r requirements.txt
```

## 使用

```
python darklink.py -h

options:
  -h, --help            show this help message and exit
  -i I                  输入目标文件
  -o O                  输出报告文件
  -x PROXY, --proxy PROXY
                        代理地址，例如 http://127.0.0.1:8080
  -I, --info            启用详细输出模式（显示所有扫描页面处理信息）
```

```bash
python darklink.py -i targets.txt -o report.md
```
