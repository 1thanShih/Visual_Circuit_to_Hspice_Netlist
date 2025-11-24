# Python Circuit CAD (HSPICE Generator)

一個超輕量級的電路圖繪製工具，專門用來生成 HSPICE Netlist。
使用 Python 原生 Tkinter 開發，無需安裝大型 EDA 軟體。

## 🚀 快速啟動 (Quick Start)

### Windows 使用者
直接雙擊執行目錄下的 **`run.bat`**。
它會自動檢查並建立需要的 Conda 環境 (修正 Tcl/Tk 錯誤)。

### 進階使用者
```bash
conda create -n circuit_cad python=3.11 tk -y
conda activate circuit_cad
python main.py