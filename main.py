import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from parser import Parser

class ParserGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("C Parser & Intermediate Code Generator")
        self.root.geometry("1300x800")

        self.create_layout()

    def create_layout(self):
        # ==== MAIN SPLIT FRAME ====
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill='both', expand=True)

        left_frame = tk.Frame(main_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        right_frame = tk.Frame(main_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)

        # ==== LEFT SIDE ====
        # Code Editor
        code_frame = tk.LabelFrame(left_frame, text="C Code Editor", font=("Arial", 12, "bold"))
        code_frame.pack(fill='x', padx=5, pady=5)
        self.text_area = scrolledtext.ScrolledText(code_frame, width=80, height=15, font=("Courier New", 11))
        self.text_area.pack(padx=5, pady=5, fill='x')

        self.submit_btn = tk.Button(
            left_frame, text="Parse and Generate",
            command=self.parse_code,
            font=("Arial", 12, "bold"),
            bg="#007acc", fg="white"
        )
        self.submit_btn.pack(pady=5)

        # Token Table
        token_frame = tk.LabelFrame(left_frame, text="Tokens by Line", font=("Arial", 12, "bold"))
        token_frame.pack(fill='both', expand=True, padx=5, pady=5)

        columns = ("Line", "Token Type", "Token Value")
        self.token_tree = ttk.Treeview(token_frame, columns=columns, show='headings', height=10)
        for col in columns:
            self.token_tree.heading(col, text=col)
            self.token_tree.column(col, width=100 if col != "Token Value" else 300, anchor='w')
        self.token_tree.pack(padx=5, pady=5, fill='both', expand=True)

        # ==== RIGHT SIDE ====
        # Symbol Table
        symbol_frame = tk.LabelFrame(right_frame, text="Symbol Table", font=("Arial", 12, "bold"))
        symbol_frame.pack(fill='both', expand=True, padx=5, pady=5)

        sym_columns = ("Symbol Name", "Symbol Type")
        self.symbol_tree = ttk.Treeview(symbol_frame, columns=sym_columns, show='headings', height=10)
        for col in sym_columns:
            self.symbol_tree.heading(col, text=col)
            self.symbol_tree.column(col, width=150, anchor='w')
        self.symbol_tree.pack(padx=5, pady=5, fill='both', expand=True)

        # Intermediate Code
        ir_frame = tk.LabelFrame(right_frame, text="Intermediate Code", font=("Arial", 12, "bold"))
        ir_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.ir_output = scrolledtext.ScrolledText(ir_frame, font=("Courier", 10), height=12, state='disabled', bg="#f9f9f9")
        self.ir_output.pack(padx=5, pady=5, fill='both', expand=True)

    def parse_code(self):
        code = self.text_area.get("1.0", tk.END).strip()
        if not code:
            messagebox.showwarning("Input Error", "Please enter C code before submitting.")
            return

        parser = Parser()

        # Clear old output
        self.token_tree.delete(*self.token_tree.get_children())
        self.symbol_tree.delete(*self.symbol_tree.get_children())
        self.set_text(self.ir_output, "")

        try:
            lines = code.split('\n')
            for line_number, line in enumerate(lines, 1):
                stripped = line.strip()
                if not stripped:
                    continue

                # Tokenize and show tokens
                tokens = parser.lexer.tokenize(stripped)
                for token in tokens:
                    self.token_tree.insert("", "end", values=(line_number, token[0], token[1]))

                parser.parse_line(stripped, line_number)

            parser.validate_main()

            # Symbol Table Display (Tree)
            for symbol, kind in parser.symbol_table.items():
                self.symbol_tree.insert("", "end", values=(symbol, kind))

            # Intermediate code
            parser.write_intermediate_code()
            with open("intermediate_code.txt", "r") as f:
                self.set_text(self.ir_output, f.read().strip())

            messagebox.showinfo("Success", "Parsing successful. Intermediate code generated.")

        except SyntaxError as e:
            messagebox.showerror("Syntax Error", str(e))

    def set_text(self, widget, content):
        widget.config(state='normal')
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, content)
        widget.config(state='disabled')

def main():
    root = tk.Tk()
    app = ParserGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
