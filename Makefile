# 定義環境名稱
ENV_NAME = circuit_cad
# 指定 Python 版本 (建議 3.11，比 3.13 穩定且支援度高)
PYTHON_VER = 3.11

# 預設目標：如果只打 make，會執行 setup 和 run
all: setup run

# 1. 建立環境並安裝 tk
# 注意：我們顯式要求安裝 'tk' 套件，這能修復 TclError
setup:
	@echo "Checking/Creating Conda environment: $(ENV_NAME)..."
	conda create -n $(ENV_NAME) python=$(PYTHON_VER) tk -y || echo "Environment might already exist."

# 2. 執行程式
# 使用 'conda run' 可以不用手動 activate 就執行指令
run:
	@echo "Starting Circuit CAD..."
	conda run -n $(ENV_NAME) python main.py

# 清除環境 (若想重來)
clean:
	conda env remove -n $(ENV_NAME) -y