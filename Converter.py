from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import os
import base64
from tkinter.messagebox import showerror, showinfo
import pyperclip

# === Глобальные переменные ===
User_path = ""
path = ""
current_mode = None  # True — один файл, False — несколько
progress_bar = None
main_window = None  # Главное окно (глобальное для доступа из функций)
# Глобальные виджеты
editor = None
directory_label = None
user_path_label = None
convert_button = None
result_label = None

# === Функции ===

def select_user_dir():
    """Выбор директории для сохранения."""
    global User_path
    selected_path = filedialog.askdirectory()
    if selected_path:
        if not os.access(selected_path, os.W_OK):
            showerror(title="Ошибка", message=f"Нет прав на запись в директорию:\n{selected_path}")
            return
        User_path = selected_path
        user_path_label.config(text=f"✅ Сохраняется в: {User_path}", fg="#008000")
        update_button_states()

def copy_to_clipboard():
    """Копирование пути в буфер обмена."""
    if User_path:
        pyperclip.copy(User_path)
        result_label.config(text="📋 Путь скопирован в буфер обмена", bg="#c8f7c5")
    else:
        result_label.config(text="❌ Выберите директорию для сохранения", bg="#ffcccc")

def one_file_convert(result_label_widget):
    global progress_bar
    if not User_path:
        showerror(title="Ошибка", message="Сначала выберите директорию для сохранения!")
        return

    file = filedialog.askopenfilename(
        title="Выберите файл для конвертации",
        filetypes=[("Все файлы", "*.*")]
    )
    if not file:
        return

    # Показать прогресс-бар
    progress_bar.pack(anchor=W, padx=20, pady=(0, 10))
    result_label_widget.config(text="Конвертирую файл...", bg="#d1ecf1")
    main_window.update_idletasks()

    try:
        with open(file, "rb") as f:
            file_data = f.read()
        base64_string = base64.b64encode(file_data).decode("utf-8")

        output_filename = f"{os.path.splitext(os.path.basename(file))[0]}.base64.txt"
        output_path = os.path.join(User_path, output_filename)

        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(base64_string)

        # Обновляем прогресс
        progress_bar['value'] = 1
        progress_bar['maximum'] = 1
        main_window.update_idletasks()

        result_label_widget.config(text=f"✅ Файл успешно сконвертирован!\n{output_path}", bg="#c8f7c5")
        showinfo("Успех", f"Файл сохранён как:\n{output_path}")

    except Exception as e:
        result_label_widget.config(text=f"❌ Ошибка: {e}", bg="#ffcccc")
        showerror("Ошибка", f"Не удалось сконвертировать файл:\n{e}")
    finally:
        progress_bar.pack_forget()  # Скрыть

def open_directory():
    """Выбор исходной директории."""
    global path
    selected_path = filedialog.askdirectory()
    if selected_path:
        path = selected_path
        directory_label.config(text=f"✅ Исходная директория: {path}", fg="#008000")
        update_button_states()

def encode_dir(result_label_widget):
    global progress_bar
    if not User_path:
        showerror(title="Ошибка", message="Сначала выберите директорию для сохранения!")
        return
    if not path:
        showerror(title="Ошибка", message="Сначала выберите исходную директорию!")
        return

    extension = editor.get("1.0", END).strip()

    # Собираем подходящие файлы
    files_to_process = []
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if os.path.isfile(file_path) and (not extension or file.endswith(f".{extension}")):
            files_to_process.append(file)

    if not files_to_process:
        result_label_widget.config(text="❌ Нет подходящих файлов для конвертации", bg="#ffcccc")
        return

    total = len(files_to_process)
    progress_bar['maximum'] = total
    progress_bar.pack(anchor=W, padx=20, pady=(0, 10))
    result_label_widget.config(text=f"Начинаю конвертацию {total} файлов...", bg="#fff3cd")
    main_window.update_idletasks()

    count = 0
    try:
        for file in files_to_process:
            file_path = os.path.join(path, file)
            try:
                with open(file_path, "rb") as f:
                    file_data = f.read()
                base64_string = base64.b64encode(file_data).decode("utf-8")

                output_filename = f"{os.path.splitext(file)[0]}.base64.txt"
                output_path = os.path.join(User_path, output_filename)

                with open(output_path, "w", encoding="utf-8") as output_file:
                    output_file.write(base64_string)

                count += 1
                progress_bar['value'] = count
                result_label_widget.config(text=f"Обработано: {count} из {total}", bg="#d1ecf1")
                main_window.update_idletasks()

            except Exception as e:
                result_label_widget.config(text=f"⚠️ Ошибка при обработке '{file}': {e}", bg="#ffeaa7")
                main_window.update_idletasks()

        result_label_widget.config(text=f"✅ Успешно сконвертировано {count} файлов!", bg="#c8f7c5")
        showinfo("Готово!", f"Конвертация завершена!\nСохранено файлов: {count}")

    except Exception as e:
        result_label_widget.config(text=f"❌ Критическая ошибка: {e}", bg="#ffcccc")
        showerror("Ошибка", f"Не удалось завершить конвертацию:\n{e}")
    finally:
        progress_bar.pack_forget()  # Скрыть

def update_button_states():
    """Обновляет состояние кнопки 'Конвертировать'."""
    if current_mode is None:
        return
    if current_mode:  # Один файл
        convert_button.config(state="normal" if User_path else "disabled")
    else:  # Несколько файлов
        convert_button.config(state="normal" if User_path and path else "disabled")

def start_one_file_window():
    ask_window.destroy()
    create_main_window(one_file_mode=True)

def start_multiple_files_window():
    ask_window.destroy()
    create_main_window(one_file_mode=False)

def go_back_to_ask_window(window_to_close):
    window_to_close.destroy()
    create_ask_window()

def create_ask_window():
    """Стартовое окно выбора режима."""
    global ask_window
    ask_window = Tk()
    ask_window.title("Конвертер Base64")
    ask_window.geometry("300x150")
    ask_window.resizable(False, False)
    ask_window.configure(bg="#f9f9f9")

    Label(ask_window, text="Что вы хотите сделать?", font=("Segoe UI", 12, "bold"), bg="#f9f9f9").pack(pady=10)
    ttk.Button(ask_window, text="📁 Конвертировать один файл", command=start_one_file_window, width=30).pack(pady=5)
    ttk.Button(ask_window, text="📂 Конвертировать несколько файлов", command=start_multiple_files_window, width=35).pack(pady=5)

    ask_window.mainloop()

def create_main_window(one_file_mode):
    global main_window, current_mode, progress_bar
    global editor, directory_label, user_path_label, convert_button, result_label

    current_mode = one_file_mode
    main_window = Tk()
    main_window.title("Конвертер файлов в Base64")
    main_window.geometry("500x500")
    main_window.resizable(False, False)
    main_window.configure(bg="#ffffff")

    # Заголовок
    header = Label(main_window, text="Конвертер файлов в Base64", font=("Segoe UI", 16, "bold"), bg="#ffffff", fg="#2c3e50")
    header.pack(pady=(10, 5))

    # Подсказка (только для множественной конвертации)
    if not one_file_mode:
        instruction = Label(
            main_window,
            text="Введите формат файлов (например: docx)\nОставьте пустым — чтобы сконвертировать ВСЕ файлы:",
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#7f8c8d",
            justify=LEFT
        )
        instruction.pack(anchor=W, padx=20, pady=(0, 5))

    # Поле ввода расширения
    editor = Text(main_window, height=1, width=15, wrap=WORD, font=("Segoe UI", 10), relief="groove", bd=2)
    if not one_file_mode:
        editor.pack(anchor=W, padx=20, pady=(0, 10))

    # Кнопка выбора исходной директории
    if not one_file_mode:
        open_directory_button = ttk.Button(main_window, text="📁 Выбрать исходную директорию", command=open_directory)
        open_directory_button.pack(anchor=W, padx=20, pady=(0, 5))

        directory_label = Label(main_window, text="Исходная директория не выбрана", font=("Segoe UI", 9), bg="#ffffff", fg="#e74c3c")
        directory_label.pack(anchor=W, padx=20, pady=(0, 10))

    # Кнопка выбора директории для сохранения
    user_path_button = ttk.Button(main_window, text="📁 Выбрать директорию для сохранения", command=select_user_dir)
    user_path_button.pack(anchor=W, padx=20, pady=(0, 5))

    # Метка директории сохранения
    user_path_label = Label(main_window, text="Директория куда сохраняются файлы", font=("Segoe UI", 9), bg="#ffffff", fg="#e74c3c")
    user_path_label.pack(anchor=W, padx=20, pady=(0, 10))

    # Кнопка конвертации
    if one_file_mode:
        convert_button = ttk.Button(main_window, text="🔄 Конвертировать файл", command=lambda: one_file_convert(result_label))
    else:
        convert_button = ttk.Button(main_window, text="🔄 Конвертировать файлы", command=lambda: encode_dir(result_label))
    convert_button.pack(anchor=W, padx=20, pady=(0, 10))

    # Прогресс-бар
    progress_bar = ttk.Progressbar(main_window, orient=HORIZONTAL, length=460, mode='determinate')
    progress_bar.pack(anchor=W, padx=20, pady=(0, 10))
    progress_bar.pack_forget()  # Скрыт по умолчанию

    # Результат
    result_label = Label(
        main_window,
        text="Здесь появится результат работы программы",
        font=("Segoe UI", 10),
        bg="#f0f0f0",
        fg="#34495e",
        relief="solid",
        bd=1,
        padx=10,
        pady=5,
        wraplength=460,
        justify=LEFT
    )
    result_label.pack(anchor=W, padx=20, pady=(10, 10), fill=X)

    # Кнопка копирования пути
    copy_to_clipboard_button = ttk.Button(main_window, text="📋 Скопировать путь сохранения", command=copy_to_clipboard)
    copy_to_clipboard_button.pack(anchor=W, padx=20, pady=(0, 10))

    # Кнопка «Назад»
    back_button = ttk.Button(main_window, text="← Назад", command=lambda: go_back_to_ask_window(main_window))
    back_button.pack(anchor=W, padx=20, pady=(10, 20))

    # Обновить состояние кнопки
    update_button_states()

    main_window.mainloop()

# === Запуск программы ===
if __name__ == "__main__":
    create_ask_window()