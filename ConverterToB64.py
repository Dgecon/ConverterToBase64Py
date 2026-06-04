from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import os
import base64
from tkinter.messagebox import showerror, showinfo
import pyperclip
import win32clipboard
import struct
import datetime
import sys
IS_WINDOWS = sys.platform == "win32"

# Попытка импорта pywin32 только на Windows
pywin32_available = False
if IS_WINDOWS:
    try:
        pywin32_available = True
    except ImportError:
        print("Библиотека pywin32 не найдена. Установите её: pip install pywin32")

#Утилита: позиционирование окна рядом с курсором
def place_window_near_cursor(window, width, height, dx=12, dy=12, screen_margin=20):
    """
    Размещает окно рядом с курсором мыши, не допуская выхода за границы экрана.

    :param window: экземпляр Tk/Toplevel
    :param width: ширина окна
    :param height: высота окна
    :param dx, dy: смещение от курсора (в пикселях)
    :param screen_margin: минимальный отступ от краёв экрана
    """
    x, y = window.winfo_pointerxy()

    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    win_x = x + dx
    win_y = y + dy

    if win_x + width > screen_width - screen_margin:
        win_x = screen_width - width - screen_margin

    if win_y + height > screen_height - screen_margin:
        win_y = screen_height - height - screen_margin

    
    if win_x < screen_margin:
        win_x = screen_margin

    
    if win_y < screen_margin:
        win_y = screen_margin

    window.geometry(f"{width}x{height}+{win_x}+{win_y}")
# === Глобальные переменные ===
last_converted_file = None  # Для режима одного файла
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
copy_text_button = None


def copy_files_to_clipboard(file_paths):
    """
    Копирует список файлов в буфер обмена Windows в формате CF_HDROP (как делает Проводник).
    Работает на всех версиях pywin32.
    """
    if not file_paths:
        return False

    try:
        
        valid_paths = []
        for p in file_paths:
            clean_path = os.path.abspath(os.path.normpath(p))
            if os.path.exists(clean_path):
                valid_paths.append(clean_path)
            else:
                print(f"Файл не найден: {clean_path}")
        
        if not valid_paths:
            return False

        
        
        
        
        
        
        dropfiles_header = struct.pack("IIIII", 20, 0, 0, 0, 1)

        
        
        file_list = "\0".join(valid_paths) + "\0\0"
        file_bytes = file_list.encode("utf-16le")

        
        clipboard_data = dropfiles_header + file_bytes

        
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_HDROP, clipboard_data)
        win32clipboard.CloseClipboard()
        return True

    except Exception as e:
        print(f"Ошибка при копировании файлов: {e}")
        return False

# === Вспомогательная функция: получить список сконвертированных файлов ===
def get_converted_files(save_dir=None):
    """
    Возвращает список .base64.txt файлов в каталоге сохранения.
    По умолчанию использует выбранный каталог, иначе исходный (path).
    """
    target_dir = save_dir or User_path or path
    if not target_dir or not os.path.isdir(target_dir):
        return []
    return [
        os.path.join(target_dir, f)
        for f in os.listdir(target_dir)
        if f.endswith('.base64.txt')
    ]

# === Функции интерфейса ===

def select_user_dir():
    global User_path
    selected_path = filedialog.askdirectory()
    if selected_path:
        if not os.access(selected_path, os.W_OK):
            showerror(title="Ошибка", message=f"Нет прав на запись в директорию:\n{selected_path}")
            return
        User_path = selected_path
        user_path_label.config(text=f"Сохраняется в: {User_path}", fg="#008000")
        update_button_states()

def copy_to_clipboard():
    if User_path:
        pyperclip.copy(User_path)
        result_label.config(text="Путь сохранения скопирован", bg="#c8f7c5")
    else:
        result_label.config(text="Директория не выбрана", bg="#ffcccc")

def copy_converted_files():
    if current_mode is None:
        result_label.config(text="Режим не определён", bg="#ffcccc")
        return

    if current_mode:
        
        if last_converted_file and os.path.exists(last_converted_file):
            files = [last_converted_file]
        else:
            result_label.config(text="Нет последнего сконвертированного файла", bg="#ffcccc")
            return
    else:
        
        files = get_converted_files()
        if not files:
            result_label.config(text="Нет сконвертированных файлов", bg="#ffcccc")
            return

    print("Попытка скопировать файлы:", files)

    if IS_WINDOWS and pywin32_available:
        success = copy_files_to_clipboard(files)
        print("Результат копирования (pywin32):", success)
        if success:
            result_label.config(text=f"Скопировано {len(files)} файл(ов)", bg="#c8f7c5")
            showinfo("Готово", "Файлы скопированы! Вставьте в проводник (Ctrl+V).")
        else:
            pyperclip.copy('\n'.join(files))
            result_label.config(text="Скопировано как текст", bg="#ffeaa7")
    else:
        pyperclip.copy('\n'.join(files))
        result_label.config(text="Пути скопированы (как текст)", bg="#ffeaa7")

def copy_last_converted_text():
    """
    Копирует содержимое последнего сконвертированного файла (one file mode) как строку.
    """
    if not last_converted_file or not os.path.exists(last_converted_file):
        result_label.config(text="Нет последнего сконвертированного файла", bg="#ffcccc")
        return
    try:
        with open(last_converted_file, "r", encoding="utf-8") as f:
            data = f.read()
        pyperclip.copy(data)
        result_label.config(text="Содержимое скопировано в буфер обмена", bg="#c8f7c5")
    except Exception as e:
        result_label.config(text=f"Не удалось скопировать: {e}", bg="#ffcccc")

def one_file_convert(result_label_widget):
    global progress_bar, last_converted_file  
    file = filedialog.askopenfilename(
        title="Выберите файл для конвертации",
        filetypes=[("Все файлы", "*.*")]
    )
    if not file:
        return

    progress_bar.pack(anchor=W, padx=20, pady=(0, 10))
    result_label_widget.config(text="Конвертирую файл...", bg="#d1ecf1")
    main_window.update_idletasks()

    try:
        with open(file, "rb") as f:
            file_data = f.read()
        base64_string = base64.b64encode(file_data).decode("utf-8")

        save_dir = User_path if User_path else os.path.dirname(file)
        output_filename = f"{os.path.splitext(os.path.basename(file))[0]}-{datetime.date.today()}.base64.txt"
        output_path = os.path.join(save_dir, output_filename)

        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(base64_string)

        
        last_converted_file = output_path
        update_button_states()

        progress_bar['value'] = 1
        progress_bar['maximum'] = 1
        main_window.update_idletasks()

        result_label_widget.config(text=f"Файл успешно сконвертирован!\n{output_path}", bg="#c8f7c5")
        showinfo("Успех", f"Файл сохранён как:\n{output_path}")

    except Exception as e:
        result_label_widget.config(text=f"Ошибка: {e}", bg="#ffcccc")
        showerror("Ошибка", f"Не удалось сконвертировать файл:\n{e}")
    finally:
        progress_bar.pack_forget()

def open_directory():
    global path
    selected_path = filedialog.askdirectory()
    if selected_path:
        path = selected_path
        directory_label.config(text=f"Исходная директория: {path}", fg="#008000")
        update_button_states()

def encode_dir(result_label_widget):
    global progress_bar
    if not path:
        showerror(title="Ошибка", message="Сначала выберите исходную директорию!")
        return

    extension = editor.get("1.0", END).strip()

    files_to_process = []
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if os.path.isfile(file_path) and (not extension or file.endswith(f".{extension}")):
            files_to_process.append(file)

    if not files_to_process:
        result_label_widget.config(text="Нет подходящих файлов", bg="#ffcccc")
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

                save_dir = User_path if User_path else path
                output_filename = f"{os.path.splitext(file)[0]}-{datetime.date.today()}.base64.txt"
                output_path = os.path.join(save_dir, output_filename)

                with open(output_path, "w", encoding="utf-8") as output_file:
                    output_file.write(base64_string)

                count += 1
                progress_bar['value'] = count
                result_label_widget.config(text=f"Обработано: {count} из {total}", bg="#d1ecf1")
                main_window.update_idletasks()

            except Exception as e:
                result_label_widget.config(text=f"Ошибка при обработке '{file}': {e}", bg="#ffeaa7")
                main_window.update_idletasks()

        result_label_widget.config(text=f"Успешно сконвертировано {count} файлов!", bg="#c8f7c5")
        showinfo("Готово!", f"Конвертация завершена!\nСохранено файлов: {count}")

    except Exception as e:
        result_label_widget.config(text=f"Критическая ошибка: {e}", bg="#ffcccc")
        showerror("Ошибка", f"Не удалось завершить конвертацию:\n{e}")
    finally:
        progress_bar.pack_forget()

def update_button_states():
    global copy_text_button
    if current_mode is None:
        return
    if current_mode:
        convert_button.config(state="normal")
        if copy_text_button:
            copy_text_button.config(state="normal" if last_converted_file else "disabled")
    else:
        convert_button.config(state="normal" if path else "disabled")

def start_one_file_window():
    global last_converted_file
    last_converted_file = None
    ask_window.destroy()
    create_main_window(one_file_mode=True)

def start_multiple_files_window():
    global last_converted_file
    last_converted_file = None
    ask_window.destroy()
    create_main_window(one_file_mode=False)

def go_back_to_ask_window(window_to_close):
    window_to_close.destroy()
    create_ask_window()

def show_help_window():
    """Открывает окно со справкой по использованию программы."""
    help_win = Toplevel()
    help_win.title("Справка по программе")
    help_win.geometry("520x420")
    help_win.resizable(False, False)
    help_win.configure(bg="#ffffff")

    # Заголовок
    Label(help_win, text="Инструкция по использованию", font=("Segoe UI", 14, "bold"), bg="#ffffff").pack(pady=(10, 10))

    # Текст справки
    help_text = Text(help_win, wrap=WORD, font=("Segoe UI", 10), bg="#ffffff", relief="flat")
    help_text.pack(padx=20, pady=(0, 10), fill=BOTH, expand=True)

    instructions = """ Режим "Конвертировать один файл"
1. Нажмите "Выбрать файл для конвертации".
2. Выберите любой файл в проводнике.
3. Программа создаст .base64.txt файл рядом (или в выбранной папке сохранения).
4. Используйте:
   - «Копировать результаты» — чтобы скопировать файл в проводник (Ctrl+V).
   - «Копировать содержимое как строку» — чтобы вставить Base64 в код/чат.

Режим "Конвертировать несколько файлов"
1. Укажите формат (например: pdf) или оставьте пустым для всех файлов.
2. Нажмите "Выбрать исходную директорию".
3. Нажмите "Конвертировать файлы".
4. Результаты сохранятся в указанной папке (или в исходной).
5. Нажмите «Копировать результаты», чтобы вставить все сконвертированные файлы в другую папку.

Папка сохранения (опционально)
- Если не указана — файлы сохраняются в исходной директории.
- Указав её, вы управляете, куда попадут результаты.

Советы
- Имена файлов дополняются датой (например: doc-2025-04-05.base64.txt).
- Все файлы копируются в формате, понятном Проводнику Windows (требуется pywin32).
- При ошибке копирования — путь/содержимое копируется как текст.
"""

    help_text.insert("1.0", instructions)
    help_text.config(state=DISABLED)  

    
    ttk.Button(help_win, text="Закрыть", command=help_win.destroy).pack(pady=(0, 10))

def create_ask_window():
    global ask_window
    ask_window = Tk()
    ask_window.title("Конвертер Base64")
    place_window_near_cursor(ask_window, 320, 150, screen_margin=300)
    ask_window.resizable(False, False)
    ask_window.configure(bg="#f9f9f9")

    Label(ask_window, text="Что вы хотите сделать?", font=("Segoe UI", 12, "bold"), bg="#f9f9f9").pack(pady=10)
    ttk.Button(ask_window, text="Конвертировать один файл", command=start_one_file_window, width=30).pack(pady=5)
    ttk.Button(ask_window, text="Конвертировать несколько файлов", command=start_multiple_files_window, width=35).pack(pady=5)
    ask_window.mainloop()

def create_main_window(one_file_mode):
    global main_window, current_mode, progress_bar
    global editor, directory_label, user_path_label, convert_button, result_label, copy_text_button

    current_mode = one_file_mode
    main_window = Tk()
    main_window.title("Конвертер файлов в Base64")
    place_window_near_cursor(main_window, 500, 530 if one_file_mode else 630, screen_margin=100)
    main_window.resizable(False, False)
    main_window.configure(bg="#ffffff")

    header = Label(main_window, text="Конвертер файлов в Base64", font=("Segoe UI", 16, "bold"), bg="#ffffff", fg="#2c3e50")
    header.pack(pady=(10, 5))

    save_frame = ttk.LabelFrame(main_window, text="Куда сохранять", padding=(10, 8))
    save_frame.pack(anchor=W, padx=20, pady=(5, 10), fill=X)
    user_path_button = ttk.Button(save_frame, text="Выбрать директорию для сохранения", command=select_user_dir)
    user_path_button.pack(anchor=W, pady=(0, 5))
    user_path_label = Label(
        save_frame,
        text="Директория для сохранения (необязательно, иначе исходная)",
        font=("Segoe UI", 9),
        bg="#ffffff",
        fg="#7f8c8d"
    )
    user_path_label.pack(anchor=W)

    source_frame = ttk.LabelFrame(main_window, text="Что конвертируем", padding=(10, 8))
    source_frame.pack(anchor=W, padx=20, pady=(0, 10), fill=X)
    if one_file_mode:
        # В режиме одного файла кнопку сразу используем для выбора файла
        convert_button = ttk.Button(source_frame, text="Выбрать файл для конвертации", command=lambda: one_file_convert(result_label))
        convert_button.pack(anchor=W, pady=(0, 5))
    else:
        instruction = Label(
            source_frame,
            text="Введите формат файлов для фильтрации(например: docx)\nОставьте пустым — чтобы сконвертировать ВСЕ файлы:",
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#7f8c8d",
            justify=LEFT
        )
        instruction.pack(anchor=W, pady=(0, 5))

        editor = Text(source_frame, height=1, width=15, wrap=WORD, font=("Segoe UI", 10), relief="groove", bd=2)
        editor.pack(anchor=W, pady=(0, 8))

        open_directory_button = ttk.Button(source_frame, text="Выбрать исходную директорию", command=open_directory)
        open_directory_button.pack(anchor=W, pady=(0, 5))
        directory_label = Label(source_frame, text="Исходная директория не выбрана", font=("Segoe UI", 9), bg="#ffffff", fg="#e74c3c")
        directory_label.pack(anchor=W, pady=(0, 5))

        convert_button = ttk.Button(source_frame, text="Конвертировать файлы", command=lambda: encode_dir(result_label))
        convert_button.pack(anchor=W, pady=(5, 0))

    actions_frame = ttk.LabelFrame(main_window, text="Действия с результатом", padding=(10, 8))
    actions_frame.pack(anchor=W, padx=20, pady=(0, 10), fill=X)

    copy_files_button = ttk.Button(actions_frame, text="Копировать результаты", command=copy_converted_files)
    copy_files_button.pack(anchor=W, pady=(0, 6))
    copy_text_button = None
    if one_file_mode:
        copy_text_button = ttk.Button(actions_frame, text="Копировать содержимое как строку", command=copy_last_converted_text)
        copy_text_button.pack(anchor=W, pady=(0, 6))
        copy_text_button.config(state="disabled")

    copy_to_clipboard_button = ttk.Button(actions_frame, text="Скопировать путь сохранения", command=copy_to_clipboard)
    copy_to_clipboard_button.pack(anchor=W, pady=(0, 0))

    progress_bar = ttk.Progressbar(main_window, orient=HORIZONTAL, length=460, mode='determinate')
    progress_bar.pack(anchor=W, padx=20, pady=(0, 10))
    progress_bar.pack_forget()

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

    copy_to_clipboard_button = ttk.Button(main_window, text="Скопировать путь сохранения", command=copy_to_clipboard)
    copy_to_clipboard_button.pack(anchor=W, padx=20, pady=(0, 10))
        # Кнопка "Справка"
    help_button = ttk.Button(main_window, text="? Справка", command=show_help_window)
    help_button.pack(anchor=W, padx=20, pady=(0, 5))

    # Кнопка "Назад"
    back_button = ttk.Button(main_window, text="← Назад", command=lambda: go_back_to_ask_window(main_window))
    back_button.pack(anchor=W, padx=20, pady=(0, 20))


    update_button_states()
    main_window.mainloop()

if __name__ == "__main__":
    create_ask_window()