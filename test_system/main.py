import tkinter as tk
from tkinter import ttk, messagebox
from database import init_db
from services import (
    create_test,
    get_tests,
    add_question,
    get_questions,
    get_question_count,
    save_result,
    get_results,
    update_question,
    delete_question,
)
from proxy import TestProxy
from engine import TestRunner
from models import User, Test


init_db()


class GUIRunner(TestRunner):
    def __init__(self, root, current_user, test_obj):
        self.root = root
        self.current_user = current_user
        self.test_obj = test_obj
        self.questions = get_questions(test_obj.id)
        self.current_index = 0

    def run(self, questions=None):
        if not self.questions:
            messagebox.showerror("Помилка", "У цьому тесті немає питань.")
            return
        super().run(self.questions)

    def ask(self, question):
        answer_holder = {"value": None, "cancelled": False}

        win = tk.Toplevel(self.root)
        win.title(f"Проходження тесту: {self.test_obj.title}")
        win.geometry("620x520")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        def on_close():
            confirm = messagebox.askyesno("Підтвердження", "Скасувати проходження тесту?")
            if confirm:
                answer_holder["cancelled"] = True
                win.destroy()

        win.protocol("WM_DELETE_WINDOW", on_close)

        container = tk.Frame(win, padx=20, pady=20)
        container.pack(fill="both", expand=True)

        tk.Label(
            container,
            text=self.test_obj.title,
            font=("Segoe UI", 16, "bold")
        ).pack(anchor="w")

        tk.Label(
            container,
            text=f"Питання {self.current_index + 1} з {len(self.questions)}",
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(8, 8))

        progress = ttk.Progressbar(
            container,
            maximum=len(self.questions),
            value=self.current_index + 1,
            length=560
        )
        progress.pack(anchor="w", pady=(0, 16))

        meta_text = f"Складність: {question.difficulty} | Бали: {question.points}"
        tk.Label(
            container,
            text=meta_text,
            font=("Segoe UI", 9),
            foreground="#555555"
        ).pack(anchor="w", pady=(0, 10))

        tk.Label(
            container,
            text=question.text,
            font=("Segoe UI", 12),
            wraplength=560,
            justify="left"
        ).pack(anchor="w", pady=(0, 14))

        feedback_label = tk.Label(
            container,
            text="",
            font=("Segoe UI", 10, "bold")
        )
        feedback_label.pack(anchor="w", pady=(8, 4))

        explanation_label = tk.Label(
            container,
            text="",
            font=("Segoe UI", 10),
            wraplength=560,
            justify="left"
        )
        explanation_label.pack(anchor="w", pady=(0, 8))

        content_area = tk.Frame(container)
        content_area.pack(fill="x", expand=True)

        bottom = tk.Frame(container)
        bottom.pack(side="bottom", fill="x", pady=(20, 0))

        next_button = ttk.Button(bottom)
        next_button.pack_forget()

        def go_next():
            self.current_index += 1
            win.destroy()

        next_caption = "Завершити" if self.current_index == len(self.questions) - 1 else "Далі"
        next_button.config(text=next_caption, command=go_next)

        if question.q_type == "single":
            var = tk.StringVar()

            for option in question.options:
                ttk.Radiobutton(
                    content_area,
                    text=option,
                    value=option,
                    variable=var
                ).pack(anchor="w", pady=4)

            def check_answer_action():
                if not var.get():
                    messagebox.showwarning("Увага", "Оберіть один варіант відповіді.")
                    return

                answer_holder["value"] = var.get()
                is_correct = question.check_answer(answer_holder["value"])

                if is_correct:
                    feedback_label.config(text="Правильно", foreground="green")
                else:
                    feedback_label.config(
                        text=f"Неправильно. Правильна відповідь: {question.correct}",
                        foreground="red"
                    )

                if question.explanation:
                    explanation_label.config(text=f"Пояснення: {question.explanation}")

                check_button.config(state="disabled")
                next_button.pack(side="right")

        else:
            tk.Label(
                content_area,
                text="Ваша відповідь:",
                font=("Segoe UI", 10)
            ).pack(anchor="w", pady=(4, 6))

            entry = ttk.Entry(content_area, width=72)
            entry.pack(anchor="w", pady=(0, 10))
            entry.focus()

            def check_answer_action():
                text = entry.get().strip()
                if not text:
                    messagebox.showwarning("Увага", "Введіть відповідь.")
                    return

                answer_holder["value"] = text
                is_correct = question.check_answer(answer_holder["value"])

                if is_correct:
                    feedback_label.config(text="Правильно", foreground="green")
                else:
                    feedback_label.config(
                        text=f"Неправильно. Правильна відповідь: {question.correct}",
                        foreground="red"
                    )

                if question.explanation:
                    explanation_label.config(text=f"Пояснення: {question.explanation}")

                check_button.config(state="disabled")
                entry.config(state="disabled")
                next_button.pack(side="right")

        check_button = ttk.Button(bottom, text="Перевірити", command=check_answer_action)
        check_button.pack(side="right")

        ttk.Button(bottom, text="Скасувати", command=on_close).pack(side="right", padx=8)

        self.root.wait_window(win)

        if answer_holder["cancelled"]:
            raise Exception("TEST_CANCELLED")

        return answer_holder["value"]

    def finish(self, score, total, duration):
        save_result(self.current_user.username, self.test_obj.id, score, total, duration)

        percent = round((score / total) * 100) if total > 0 else 0

        result_win = tk.Toplevel(self.root)
        result_win.title("Результат тесту")
        result_win.geometry("460x300")
        result_win.resizable(False, False)
        result_win.transient(self.root)
        result_win.grab_set()

        frame = tk.Frame(result_win, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="Тест завершено",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(0, 14))

        tk.Label(frame, text=f"Тест: {self.test_obj.title}", font=("Segoe UI", 11)).pack(anchor="w", pady=4)
        tk.Label(frame, text=f"Студент: {self.current_user.username}", font=("Segoe UI", 11)).pack(anchor="w", pady=4)
        tk.Label(frame, text=f"Набрано балів: {score} / {total}", font=("Segoe UI", 11)).pack(anchor="w", pady=4)
        tk.Label(frame, text=f"Успішність: {percent}%", font=("Segoe UI", 11)).pack(anchor="w", pady=4)
        tk.Label(frame, text=f"Час проходження: {duration} сек.", font=("Segoe UI", 11)).pack(anchor="w", pady=4)

        ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=14)

        if percent >= 80:
            result_text = "Відмінний результат"
        elif percent >= 50:
            result_text = "Нормальний результат"
        else:
            result_text = "Слабкий результат"

        tk.Label(
            frame,
            text=result_text,
            font=("Segoe UI", 11, "bold")
        ).pack()

        ttk.Button(frame, text="Закрити", command=result_win.destroy).pack(pady=(18, 0))


class TestSystemApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Система тестування студентів")
        self.root.geometry("1040x660")
        self.root.minsize(960, 600)

        self.current_user = None

        self.build_ui()
        self.load_tests()
        self.update_role_ui()

    def build_ui(self):
        self.root.configure(bg="#f3f4f6")

        header = tk.Frame(self.root, bg="#1f2937", height=76)
        header.pack(fill="x")
        header.pack_propagate(False)

        left_header = tk.Frame(header, bg="#1f2937")
        left_header.pack(side="left", fill="y", padx=18)

        tk.Label(
            left_header,
            text="Система тестування студентів",
            bg="#1f2937",
            fg="white",
            font=("Segoe UI", 18, "bold")
        ).pack(anchor="w", pady=(12, 2))

        self.user_info_label = tk.Label(
            left_header,
            text="Користувач не авторизований",
            bg="#1f2937",
            fg="#d1d5db",
            font=("Segoe UI", 10)
        )
        self.user_info_label.pack(anchor="w")

        right_header = tk.Frame(header, bg="#1f2937")
        right_header.pack(side="right", padx=18, pady=18)

        ttk.Button(
            right_header,
            text="Увійти як адміністратор",
            command=lambda: self.open_login_window("admin")
        ).pack(side="left", padx=6)

        ttk.Button(
            right_header,
            text="Увійти як студент",
            command=lambda: self.open_login_window("student")
        ).pack(side="left", padx=6)

        body = tk.Frame(self.root, bg="#f3f4f6")
        body.pack(fill="both", expand=True, padx=18, pady=18)

        sidebar = tk.Frame(body, bg="white", bd=1, relief="solid", width=260)
        sidebar.pack(side="left", fill="y", padx=(0, 14))
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="Дії",
            bg="white",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", padx=16, pady=(16, 12))

        self.btn_create_test = ttk.Button(sidebar, text="Створити тест", command=self.open_create_test_window)
        self.btn_add_question = ttk.Button(sidebar, text="Додати питання", command=self.open_add_question_window)
        self.btn_manage_questions = ttk.Button(sidebar, text="Переглянути / редагувати питання", command=self.open_questions_window)
        self.btn_start_test = ttk.Button(sidebar, text="Пройти тест", command=self.start_selected_test)
        self.btn_results = ttk.Button(sidebar, text="Історія результатів", command=self.open_results_window)
        self.btn_refresh = ttk.Button(sidebar, text="Оновити список", command=self.load_tests)

        self.info_box = tk.Label(
            sidebar,
            text="Увійди в систему, щоб побачити доступні дії.",
            justify="left",
            bg="white",
            fg="#374151",
            wraplength=220,
            font=("Segoe UI", 10)
        )
        self.info_box.pack(anchor="w", padx=16, pady=(18, 16))

        content = tk.Frame(body, bg="white", bd=1, relief="solid")
        content.pack(side="left", fill="both", expand=True)

        top_content = tk.Frame(content, bg="white")
        top_content.pack(fill="x", padx=16, pady=(16, 8))

        tk.Label(
            top_content,
            text="Список тестів",
            bg="white",
            font=("Segoe UI", 15, "bold")
        ).pack(side="left")

        self.selected_test_label = tk.Label(
            top_content,
            text="Обраний тест: немає",
            bg="white",
            fg="#374151",
            font=("Segoe UI", 10)
        )
        self.selected_test_label.pack(side="right")

        table_frame = tk.Frame(content, bg="white")
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        columns = ("id", "title", "count")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Назва тесту")
        self.tree.heading("count", text="Кількість питань")

        self.tree.column("id", width=80, anchor="center")
        self.tree.column("title", width=520, anchor="w")
        self.tree.column("count", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select_test)

    def update_role_ui(self):
        for btn in (
            self.btn_create_test,
            self.btn_add_question,
            self.btn_manage_questions,
            self.btn_start_test,
            self.btn_results,
            self.btn_refresh,
        ):
            btn.pack_forget()

        if self.current_user is None:
            self.info_box.config(text="Увійди в систему, щоб побачити доступні дії.")
            return

        if self.current_user.role == "admin":
            self.btn_create_test.pack(fill="x", padx=16, pady=6)
            self.btn_add_question.pack(fill="x", padx=16, pady=6)
            self.btn_manage_questions.pack(fill="x", padx=16, pady=6)
            self.btn_results.pack(fill="x", padx=16, pady=6)
            self.btn_refresh.pack(fill="x", padx=16, pady=6)

            self.info_box.config(
                text="Режим адміністратора:\n- створення тестів\n- додавання питань\n- редагування і видалення\n- перегляд результатів"
            )

        elif self.current_user.role == "student":
            self.btn_start_test.pack(fill="x", padx=16, pady=6)
            self.btn_results.pack(fill="x", padx=16, pady=6)
            self.btn_refresh.pack(fill="x", padx=16, pady=6)

            self.info_box.config(
                text="Режим студента:\n- вибір тесту\n- проходження тесту\n- перегляд історії результатів"
            )

    def open_login_window(self, role):
        win = tk.Toplevel(self.root)
        win.title("Авторизація")
        win.geometry("360x210")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        frame = tk.Frame(win, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        role_title = "Адміністратор" if role == "admin" else "Студент"

        tk.Label(
            frame,
            text=f"Вхід: {role_title}",
            font=("Segoe UI", 15, "bold")
        ).pack(anchor="w", pady=(0, 16))

        tk.Label(frame, text="Ім'я користувача:", font=("Segoe UI", 10)).pack(anchor="w")

        name_entry = ttk.Entry(frame, width=36)
        name_entry.pack(anchor="w", pady=(6, 18))
        name_entry.focus()

        def confirm():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Увага", "Введіть ім'я користувача.")
                return

            self.current_user = User(name, role)
            role_text = "адміністратор" if role == "admin" else "студент"
            self.user_info_label.config(text=f"Користувач: {name} | Роль: {role_text}")
            self.update_role_ui()
            win.destroy()

        buttons = tk.Frame(frame)
        buttons.pack(fill="x")

        ttk.Button(buttons, text="Увійти", command=confirm).pack(side="right")
        ttk.Button(buttons, text="Скасувати", command=win.destroy).pack(side="right", padx=8)

    def load_tests(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        tests = get_tests()
        for test in tests:
            count = get_question_count(test.id)
            self.tree.insert("", "end", values=(test.id, test.title, count))

        self.selected_test_label.config(text="Обраний тест: немає")

    def on_select_test(self, event=None):
        selected = self.tree.selection()
        if not selected:
            self.selected_test_label.config(text="Обраний тест: немає")
            return

        values = self.tree.item(selected[0], "values")
        self.selected_test_label.config(text=f"Обраний тест: {values[1]} (ID {values[0]})")

    def get_selected_test(self):
        selected = self.tree.selection()
        if not selected:
            return None

        values = self.tree.item(selected[0], "values")
        return {"id": int(values[0]), "title": values[1]}

    def open_create_test_window(self):
        proxy = TestProxy(self.current_user)
        if not proxy.can_edit():
            messagebox.showerror("Помилка", "Лише адміністратор може створювати тести.")
            return

        win = tk.Toplevel(self.root)
        win.title("Створення тесту")
        win.geometry("420x220")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        frame = tk.Frame(win, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="Створення нового тесту",
            font=("Segoe UI", 15, "bold")
        ).pack(anchor="w", pady=(0, 16))

        tk.Label(frame, text="Назва тесту:", font=("Segoe UI", 10)).pack(anchor="w")

        title_entry = ttk.Entry(frame, width=42)
        title_entry.pack(anchor="w", pady=(6, 18))
        title_entry.focus()

        def save():
            title = title_entry.get().strip()
            if not title:
                messagebox.showwarning("Увага", "Введіть назву тесту.")
                return

            create_test(title)
            self.load_tests()
            win.destroy()
            messagebox.showinfo("Готово", "Тест успішно створено.")

        buttons = tk.Frame(frame)
        buttons.pack(fill="x")

        ttk.Button(buttons, text="Зберегти", command=save).pack(side="right")
        ttk.Button(buttons, text="Скасувати", command=win.destroy).pack(side="right", padx=8)

    def open_add_question_window(self):
        proxy = TestProxy(self.current_user)
        if not proxy.can_edit():
            messagebox.showerror("Помилка", "Лише адміністратор може додавати питання.")
            return

        selected_test = self.get_selected_test()
        if not selected_test:
            messagebox.showerror("Помилка", "Спочатку обери тест.")
            return

        win = tk.Toplevel(self.root)
        win.title("Конструктор питання")
        win.geometry("720x760")
        win.minsize(720, 760)
        win.transient(self.root)
        win.grab_set()

        container = tk.Frame(win)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)

        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        frame = tk.Frame(scroll_frame, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Створення питання", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        tk.Label(frame, text=f"Тест: {selected_test['title']}").pack(anchor="w", pady=(4, 12))

        tk.Label(frame, text="Текст питання:").pack(anchor="w")
        question_text = tk.Text(frame, height=4)
        question_text.pack(fill="x", pady=6)

        row = tk.Frame(frame)
        row.pack(fill="x", pady=8)

        type_var = tk.StringVar(value="single")
        ttk.Label(row, text="Тип:").pack(side="left")
        ttk.Combobox(row, textvariable=type_var, values=["single", "text"], width=10, state="readonly").pack(side="left", padx=10)

        points_var = tk.StringVar(value="1")
        ttk.Label(row, text="Бали:").pack(side="left")
        ttk.Entry(row, textvariable=points_var, width=5).pack(side="left", padx=10)

        difficulty_var = tk.StringVar(value="medium")
        ttk.Label(row, text="Складність:").pack(side="left")
        ttk.Combobox(row, textvariable=difficulty_var, values=["easy", "medium", "hard"], width=10, state="readonly").pack(side="left", padx=10)

        options_frame = tk.LabelFrame(frame, text="Варіанти відповідей (single)")
        options_frame.pack(fill="x", pady=10)

        correct_option_var = tk.StringVar()
        option_entries = []

        for i in range(4):
            r = tk.Frame(options_frame)
            r.pack(fill="x", pady=3)

            rb = ttk.Radiobutton(r, variable=correct_option_var, value=str(i))
            rb.pack(side="left", padx=(0, 6))

            tk.Label(r, text=f"Варіант {i + 1}:", width=12, anchor="w").pack(side="left")
            entry = ttk.Entry(r)
            entry.pack(side="left", fill="x", expand=True)
            option_entries.append(entry)

        tk.Label(frame, text="Правильна відповідь (для text):").pack(anchor="w")
        correct_text_entry = ttk.Entry(frame)
        correct_text_entry.pack(fill="x", pady=6)

        tk.Label(frame, text="Пояснення / коментар після відповіді:").pack(anchor="w")
        explanation = tk.Text(frame, height=4)
        explanation.pack(fill="x", pady=6)

        create_more_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame,
            text="Після збереження одразу створити ще одне питання",
            variable=create_more_var
        ).pack(anchor="w", pady=(8, 0))

        def clear_form():
            question_text.delete("1.0", tk.END)
            points_var.set("1")
            difficulty_var.set("medium")
            type_var.set("single")
            correct_option_var.set("")
            correct_text_entry.delete(0, tk.END)
            explanation.delete("1.0", tk.END)
            for e in option_entries:
                e.delete(0, tk.END)
            toggle()

        def toggle():
            is_single = type_var.get() == "single"
            state = "normal" if is_single else "disabled"

            for e in option_entries:
                e.configure(state=state)

            for child in options_frame.winfo_children():
                for widget in child.winfo_children():
                    if isinstance(widget, ttk.Radiobutton):
                        if is_single:
                            widget.state(["!disabled"])
                        else:
                            widget.state(["disabled"])

            if is_single:
                correct_text_entry.configure(state="disabled")
            else:
                correct_text_entry.configure(state="normal")

        type_var.trace_add("write", lambda *args: toggle())
        toggle()

        bottom = tk.Frame(win, pady=10)
        bottom.pack(fill="x")

        def save():
            text = question_text.get("1.0", "end").strip()

            if not text:
                return messagebox.showwarning("Увага", "Введи питання")

            try:
                points = int(points_var.get())
                if points <= 0:
                    raise ValueError
            except ValueError:
                return messagebox.showwarning("Увага", "Бали мають бути додатним числом")

            difficulty = difficulty_var.get().strip()
            if difficulty not in ("easy", "medium", "hard"):
                return messagebox.showwarning("Увага", "Оберіть коректну складність")

            explanation_text = explanation.get("1.0", "end").strip()

            if type_var.get() == "single":
                options = [e.get().strip() for e in option_entries if e.get().strip()]
                if len(options) < 2:
                    return messagebox.showwarning("Увага", "Для single потрібно хоча б 2 варіанти")

                selected_index = correct_option_var.get()
                if selected_index == "":
                    return messagebox.showwarning("Увага", "Обери правильний варіант кліком")

                selected_index = int(selected_index)
                raw_values = [e.get().strip() for e in option_entries]

                if selected_index >= len(raw_values) or not raw_values[selected_index]:
                    return messagebox.showwarning("Увага", "Обраний правильний варіант порожній")

                correct = raw_values[selected_index]

            else:
                options = []
                correct = correct_text_entry.get().strip()
                if not correct:
                    return messagebox.showwarning("Увага", "Введи правильну відповідь для text")

            add_question(
                selected_test["id"],
                text,
                type_var.get(),
                options,
                correct,
                points,
                difficulty,
                explanation_text
            )

            self.load_tests()

            if create_more_var.get():
                clear_form()
                messagebox.showinfo("Готово", "Питання збережено. Можна створити наступне.")
            else:
                win.destroy()
                messagebox.showinfo("Готово", "Питання збережено.")

        ttk.Button(bottom, text="Готово", command=save).pack(side="right", padx=10)
        ttk.Button(bottom, text="Скасувати", command=win.destroy).pack(side="right")

    def open_questions_window(self):
        selected_test = self.get_selected_test()
        if not selected_test:
            messagebox.showerror("Помилка", "Спочатку обери тест у таблиці.")
            return

        questions = get_questions(selected_test["id"])

        win = tk.Toplevel(self.root)
        win.title("Питання тесту")
        win.geometry("1100x500")
        win.transient(self.root)

        main_frame = tk.Frame(win, padx=16, pady=16)
        main_frame.pack(fill="both", expand=True)

        tk.Label(
            main_frame,
            text=f"Питання тесту: {selected_test['title']}",
            font=("Segoe UI", 15, "bold")
        ).pack(anchor="w", pady=(0, 12))

        columns = ("id", "type", "points", "difficulty", "correct", "text")
        tree = ttk.Treeview(main_frame, columns=columns, show="headings")

        tree.heading("id", text="ID")
        tree.heading("type", text="Тип")
        tree.heading("points", text="Бали")
        tree.heading("difficulty", text="Складність")
        tree.heading("correct", text="Правильна відповідь")
        tree.heading("text", text="Текст питання")

        tree.column("id", width=50, anchor="center")
        tree.column("type", width=90, anchor="center")
        tree.column("points", width=70, anchor="center")
        tree.column("difficulty", width=100, anchor="center")
        tree.column("correct", width=170, anchor="center")
        tree.column("text", width=520, anchor="w")

        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        question_map = {}
        for q in questions:
            item_id = tree.insert("", "end", values=(q.id, q.q_type, q.points, q.difficulty, q.correct, q.text))
            question_map[item_id] = q

        buttons_frame = tk.Frame(win, padx=16, pady=10)
        buttons_frame.pack(fill="x")

        def edit_selected():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Увага", "Оберіть питання для редагування.")
                return

            question = question_map[selected[0]]
            self.open_edit_question_window(question, selected_test["title"], refresh_callback=lambda: refresh_questions())

        def delete_selected():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Увага", "Оберіть питання для видалення.")
                return

            question = question_map[selected[0]]

            confirm = messagebox.askyesno("Підтвердження", f"Видалити питання ID {question.id}?")
            if not confirm:
                return

            delete_question(question.id)
            refresh_questions()
            self.load_tests()

        def refresh_questions():
            tree.delete(*tree.get_children())
            fresh_questions = get_questions(selected_test["id"])
            question_map.clear()

            for q in fresh_questions:
                item_id = tree.insert("", "end", values=(q.id, q.q_type, q.points, q.difficulty, q.correct, q.text))
                question_map[item_id] = q

        ttk.Button(buttons_frame, text="Редагувати", command=edit_selected).pack(side="right", padx=6)
        ttk.Button(buttons_frame, text="Видалити", command=delete_selected).pack(side="right")

    def open_edit_question_window(self, question, test_title, refresh_callback):
        win = tk.Toplevel(self.root)
        win.title("Редагування питання")
        win.geometry("720x720")
        win.minsize(720, 720)
        win.transient(self.root)
        win.grab_set()

        container = tk.Frame(win)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)

        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        frame = tk.Frame(scroll_frame, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Редагування питання", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        tk.Label(frame, text=f"Тест: {test_title}").pack(anchor="w", pady=(4, 12))

        tk.Label(frame, text="Текст питання:").pack(anchor="w")
        question_text = tk.Text(frame, height=4)
        question_text.pack(fill="x", pady=6)
        question_text.insert("1.0", question.text)

        row = tk.Frame(frame)
        row.pack(fill="x", pady=8)

        type_var = tk.StringVar(value=question.q_type)
        ttk.Label(row, text="Тип:").pack(side="left")
        ttk.Combobox(row, textvariable=type_var, values=["single", "text"], width=10, state="readonly").pack(side="left", padx=10)

        points_var = tk.StringVar(value=str(question.points))
        ttk.Label(row, text="Бали:").pack(side="left")
        ttk.Entry(row, textvariable=points_var, width=5).pack(side="left", padx=10)

        difficulty_var = tk.StringVar(value=question.difficulty)
        ttk.Label(row, text="Складність:").pack(side="left")
        ttk.Combobox(row, textvariable=difficulty_var, values=["easy", "medium", "hard"], width=10, state="readonly").pack(side="left", padx=10)

        options_frame = tk.LabelFrame(frame, text="Варіанти відповідей (single)")
        options_frame.pack(fill="x", pady=10)

        correct_option_var = tk.StringVar()
        option_entries = []

        existing_options = question.options[:] if question.options else []
        while len(existing_options) < 4:
            existing_options.append("")

        selected_correct_idx = ""
        for idx, value in enumerate(existing_options):
            if value == question.correct and selected_correct_idx == "":
                selected_correct_idx = str(idx)

        for i in range(4):
            r = tk.Frame(options_frame)
            r.pack(fill="x", pady=3)

            rb = ttk.Radiobutton(r, variable=correct_option_var, value=str(i))
            rb.pack(side="left", padx=(0, 6))

            tk.Label(r, text=f"Варіант {i + 1}:", width=12, anchor="w").pack(side="left")
            entry = ttk.Entry(r)
            entry.pack(side="left", fill="x", expand=True)
            entry.insert(0, existing_options[i])
            option_entries.append(entry)

        correct_option_var.set(selected_correct_idx)

        tk.Label(frame, text="Правильна відповідь (для text):").pack(anchor="w")
        correct_text_entry = ttk.Entry(frame)
        correct_text_entry.pack(fill="x", pady=6)
        if question.q_type == "text":
            correct_text_entry.insert(0, question.correct)

        tk.Label(frame, text="Пояснення / коментар після відповіді:").pack(anchor="w")
        explanation = tk.Text(frame, height=4)
        explanation.pack(fill="x", pady=6)
        explanation.insert("1.0", question.explanation)

        def toggle():
            is_single = type_var.get() == "single"
            state = "normal" if is_single else "disabled"

            for e in option_entries:
                e.configure(state=state)

            for child in options_frame.winfo_children():
                for widget in child.winfo_children():
                    if isinstance(widget, ttk.Radiobutton):
                        if is_single:
                            widget.state(["!disabled"])
                        else:
                            widget.state(["disabled"])

            if is_single:
                correct_text_entry.configure(state="disabled")
            else:
                correct_text_entry.configure(state="normal")

        type_var.trace_add("write", lambda *args: toggle())
        toggle()

        bottom = tk.Frame(win, pady=10)
        bottom.pack(fill="x")

        def save():
            text = question_text.get("1.0", "end").strip()
            if not text:
                return messagebox.showwarning("Увага", "Введи питання")

            try:
                points = int(points_var.get())
                if points <= 0:
                    raise ValueError
            except ValueError:
                return messagebox.showwarning("Увага", "Бали мають бути додатним числом")

            difficulty = difficulty_var.get().strip()
            explanation_text = explanation.get("1.0", "end").strip()

            if type_var.get() == "single":
                raw_values = [e.get().strip() for e in option_entries]
                options = [v for v in raw_values if v]
                if len(options) < 2:
                    return messagebox.showwarning("Увага", "Для single потрібно хоча б 2 варіанти")

                selected_index = correct_option_var.get()
                if selected_index == "":
                    return messagebox.showwarning("Увага", "Обери правильний варіант")

                selected_index = int(selected_index)
                if selected_index >= len(raw_values) or not raw_values[selected_index]:
                    return messagebox.showwarning("Увага", "Обраний правильний варіант порожній")

                correct = raw_values[selected_index]
            else:
                options = []
                correct = correct_text_entry.get().strip()
                if not correct:
                    return messagebox.showwarning("Увага", "Введи правильну відповідь для text")

            update_question(
                question.id,
                text,
                type_var.get(),
                options,
                correct,
                points,
                difficulty,
                explanation_text
            )

            refresh_callback()
            self.load_tests()
            win.destroy()
            messagebox.showinfo("OK", "Питання оновлено")

        ttk.Button(bottom, text="Зберегти зміни", command=save).pack(side="right", padx=10)
        ttk.Button(bottom, text="Скасувати", command=win.destroy).pack(side="right")

    def start_selected_test(self):
        proxy = TestProxy(self.current_user)
        if not proxy.can_pass():
            messagebox.showerror("Помилка", "Лише студент може проходити тест.")
            return

        selected_test = self.get_selected_test()
        if not selected_test:
            messagebox.showerror("Помилка", "Спочатку обери тест у таблиці.")
            return

        test_obj = Test(selected_test["id"], selected_test["title"])

        if get_question_count(test_obj.id) == 0:
            messagebox.showerror("Помилка", "У вибраному тесті немає питань.")
            return

        try:
            runner = GUIRunner(self.root, self.current_user, test_obj)
            runner.run()
        except Exception as e:
            if str(e) != "TEST_CANCELLED":
                raise

    def open_results_window(self):
        win = tk.Toplevel(self.root)
        win.title("Історія результатів")
        win.geometry("920x440")
        win.transient(self.root)

        frame = tk.Frame(win, padx=16, pady=16)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="Історія проходження тестів",
            font=("Segoe UI", 15, "bold")
        ).pack(anchor="w", pady=(0, 12))

        columns = ("username", "test_id", "title", "score", "total", "duration", "date")
        tree = ttk.Treeview(frame, columns=columns, show="headings")

        tree.heading("username", text="Студент")
        tree.heading("test_id", text="ID тесту")
        tree.heading("title", text="Назва тесту")
        tree.heading("score", text="Бали")
        tree.heading("total", text="Всього")
        tree.heading("duration", text="Час (сек.)")
        tree.heading("date", text="Дата")

        tree.column("username", width=120, anchor="center")
        tree.column("test_id", width=80, anchor="center")
        tree.column("title", width=240, anchor="w")
        tree.column("score", width=70, anchor="center")
        tree.column("total", width=70, anchor="center")
        tree.column("duration", width=90, anchor="center")
        tree.column("date", width=160, anchor="center")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for row in get_results():
            tree.insert("", "end", values=(row[1], row[2], row[3], row[4], row[5], row[6], row[7]))


def main():
    root = tk.Tk()

    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    TestSystemApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()