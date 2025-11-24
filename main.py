import tkinter as tk
from editor import CircuitEditor

def main():
    root = tk.Tk()
    root.title("Python Circuit CAD v3.5 - Focus Fixed")
    root.geometry("1000x700")

    app = CircuitEditor(root)

    # 確保快捷鍵能在全域觸發
    # 使用 lambda 忽略 event 參數
    
    # 1. 元件生成
    root.bind("<r>", lambda e: app.add_comp("R"))
    root.bind("<R>", lambda e: app.add_comp("R"))
    root.bind("<l>", lambda e: app.add_comp("L"))
    root.bind("<L>", lambda e: app.add_comp("L"))
    root.bind("<c>", lambda e: app.add_comp("C"))
    root.bind("<C>", lambda e: app.add_comp("C"))
    root.bind("<n>", lambda e: app.add_comp("NMOS"))
    root.bind("<N>", lambda e: app.add_comp("NMOS"))
    root.bind("<p>", lambda e: app.add_comp("PMOS"))
    root.bind("<P>", lambda e: app.add_comp("PMOS"))

    # 2. 編輯操作 (Rotate, Mirror)
    root.bind("<m>", lambda e: app.mirror_selection())
    root.bind("<M>", lambda e: app.mirror_selection())
    # 部分鍵盤可能將旋轉視為特殊鍵，這裡多綁幾個以防萬一
    root.bind("<o>", lambda e: app.rotate_selection()) # 以防 R 鍵被佔用，增加 O (Orient)
    
    # 3. 模式切換 (Wire, Delete)
    root.bind("<w>", lambda e: app.toggle_wire_mode())
    root.bind("<W>", lambda e: app.toggle_wire_mode())
    
    root.bind("<Delete>", lambda e: app.toggle_delete_mode())
    root.bind("<Escape>", lambda e: app.set_mode("SELECT"))
    root.bind("<F1>", lambda e: app.show_help())

    # 啟動時給畫布焦點
    app.canvas.focus_set()

    root.mainloop()

if __name__ == "__main__":
    main()