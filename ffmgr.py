import os
import json
import subprocess
import sys

# --- Bảng màu Pastel (Chỉ màu chữ) ---
class UI:
    HEADER = '\033[38;2;255;182;193m'
    BLUE   = '\033[38;2;173;216;230m'
    CYAN   = '\033[38;2;175;238;238m'
    GREEN  = '\033[38;2;180;230;180m'
    YELLOW = '\033[38;2;255;255;190m'
    RED    = '\033[38;2;255;160;160m'
    WHITE  = '\033[38;2;240;240;240m'
    GRAY   = '\033[38;2;120;120;120m'
    SELECT = '\033[1m\033[38;2;255;255;100m' # Yellow
    END    = '\033[0m'
    BOLD   = '\033[1m'
    HIDE_CURSOR = '\033[?25l'
    SHOW_CURSOR = '\033[?25h'
    HOME_CURSOR = '\033[H'
    
# Định nghĩa các loại định dạng Media
class Media:
    VIDEO = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm', '.m4v', '.mpg', '.mpeg', '.3gp'}
    AUDIO = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.opus', '.wma'}
    IMAGE = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.svg'}
    ALL = VIDEO | AUDIO | IMAGE

    @staticmethod
    def get_label(filename):
        ext = os.path.splitext(filename)[1].lower()
        if ext in Media.VIDEO: return f"{UI.CYAN}[VIDEO]{UI.END}"
        if ext in Media.AUDIO: return f"{UI.GREEN}[AUDIO]{UI.END}"
        if ext in Media.IMAGE: return f"{UI.YELLOW}[IMAGE]{UI.END}"
        return f"{UI.GRAY}[FILE]{UI.END}"

# Cấu hình đường dẫn file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "ffmpeg_commands.json")

last_manual_cmd = ""
last_manual_ext = ""

def load_commands():
    commands = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding='utf-8') as f: 
                commands = json.load(f)
        except: commands = {}
    
    # Migrate data structure if needed
    updated = False
    for name, data in list(commands.items()):
        if isinstance(data, str):
            commands[name] = {"cmd": data, "ext": ".mp4"}
            updated = True
    
    if updated or not commands:
        if not commands:
            commands = {"Convert to MP4": {"cmd": "-c:v libx264 -crf 23", "ext": ".mp4"}}
        save_commands(commands)
        
    return commands

def save_commands(commands):
    with open(CONFIG_FILE, "w", encoding='utf-8') as f: 
        json.dump(commands, f, indent=4, ensure_ascii=False)

def get_key():
    """Đọc phím từ bàn phím hỗ trợ mũi tên, enter, backspace và ký tự"""
    if os.name == 'nt':
        import msvcrt
        key = msvcrt.getch()
        if key in (b'\x00', b'\xe0'):
            key = msvcrt.getch()
            return {'H': 'up', 'P': 'down', 'K': 'left', 'M': 'right'}.get(key.decode(), None)
        if key == b'\r': return 'enter'
        if key == b'\x1b': return 'esc'
        if key == b' ': return 'space'
        if key == b'\x08': return 'backspace'
        if key == b'\x03': raise KeyboardInterrupt
        try:
            char = key.decode('utf-8', 'ignore')
            if char.isprintable(): return char
        except: pass
    else:
        import tty, termios, select
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            if ch == '\x1b':
                if select.select([sys.stdin], [], [], 0.05)[0]:
                    ch2 = sys.stdin.read(2)
                    return {'[A': 'up', '[B': 'down', '[C': 'right', '[D': 'left'}.get(ch2, None)
                return 'esc'
            if ch == '\r': return 'enter'
            if ch == ' ': return 'space'
            if ch in ('\x08', '\x7f'): return 'backspace'
            if ch == '\x03': raise KeyboardInterrupt
            if ch.isprintable(): return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return None

def interactive_input(prompt, default_text=""):
    text = list(default_text)
    cursor_pos = len(text)
    
    print(UI.SHOW_CURSOR, end="")
    while True:
        display_text = "".join(text)
        print(f"\r\033[K{prompt}{display_text}", end="")
        
        move_back = len(text) - cursor_pos
        if move_back > 0:
            print(f"\033[{move_back}D", end="")
            
        sys.stdout.flush()
        
        key = get_key()
        if key == 'enter':
            print()
            print(UI.HIDE_CURSOR, end="")
            return "".join(text)
        elif key == 'esc':
            print()
            print(UI.HIDE_CURSOR, end="")
            return None
        elif key == 'backspace':
            if cursor_pos > 0:
                text.pop(cursor_pos - 1)
                cursor_pos -= 1
        elif key == 'left':
            if cursor_pos > 0:
                cursor_pos -= 1
        elif key == 'right':
            if cursor_pos < len(text):
                cursor_pos += 1
        elif key == 'space':
            text.insert(cursor_pos, ' ')
            cursor_pos += 1
        elif key and len(key) == 1:
            text.insert(cursor_pos, key)
            cursor_pos += 1

def interactive_menu(title, options, subtitle=None, max_visible=None, multi_select=False, enable_search=False):
    search_query = ""
    selected_index = 0
    selected_items = set()
    
    while True:
        filtered_indices = []
        for i, opt in enumerate(options):
            if "---" in opt:
                if not search_query: filtered_indices.append(i)
                continue
            if enable_search and search_query:
                if search_query.lower() in opt.lower():
                    filtered_indices.append(i)
            else:
                filtered_indices.append(i)
                
        num_options = len(filtered_indices)
        if num_options == 0: selected_index = 0
        elif selected_index >= num_options: selected_index = num_options - 1
            
        limit = max_visible if max_visible is not None else max(num_options, 1)
        if limit < 5: limit = 5
        
        os.system('cls' if os.name == 'nt' else 'clear')
        print(UI.HIDE_CURSOR, end="")
        
        print(f"{UI.HEADER}{UI.BOLD}=== {title} ==={UI.END}\033[K")
        if subtitle: print(f" {UI.GRAY}{subtitle}{UI.END}\033[K")
        
        if enable_search:
            print(f" {UI.YELLOW}🔍 Search:{UI.END} {search_query}█\033[K\n")
        else:
            print("\033[K")
        
        if num_options == 0:
            print(f"    {UI.GRAY}No matches found.{UI.END}\033[K")
        else:
            start_index = max(0, selected_index - limit // 2)
            end_index = start_index + limit
            if end_index > num_options:
                end_index = num_options
                start_index = max(0, end_index - limit)
                
            if start_index > 0: print(f"    {UI.CYAN}▲{UI.END}\033[K")
            else: print("\033[K")
            
            for idx in range(start_index, end_index):
                orig_idx = filtered_indices[idx]
                option = options[orig_idx]
                print('\033[K', end="")
                
                if "---" in option:
                    print(f" {UI.GRAY} {option}{UI.END}")
                    continue
                
                prefix = ""
                if multi_select:
                    prefix = f"{UI.GREEN}[x]{UI.END} " if orig_idx in selected_items else f"{UI.GRAY}[ ]{UI.END} "
                
                disp_option = option
                if idx == selected_index:
                    if UI.END in disp_option:
                        disp_option = disp_option.replace(UI.END, UI.END + UI.SELECT)
                    print(f" {UI.SELECT}➜  {prefix}{disp_option}{UI.END}")
                else:
                    if UI.END in disp_option:
                        disp_option = disp_option.replace(UI.END, UI.END + UI.WHITE)
                    print(f"    {prefix}{UI.WHITE}{disp_option}{UI.END}")
                    
            if end_index < num_options: print(f"    {UI.CYAN}▼{UI.END}\033[K")
            else: print("\033[K")
            
        scroll_info = f" | Showing {start_index+1}-{end_index} of {num_options}" if limit < num_options else ""
        help_text = "Arrows: Move | Enter: Select | Esc: Back"
        if multi_select: help_text += " | Space: Toggle"
        if enable_search: help_text += " | Type to search"
        
        print(f"{UI.CYAN}({help_text}){scroll_info}{UI.END}\033[K")
        print('\033[J', end="") 
        
        key = get_key()
        if key == 'up':
            if num_options > 0:
                selected_index = (selected_index - 1) % num_options
                while "---" in options[filtered_indices[selected_index]]:
                    selected_index = (selected_index - 1) % num_options
        elif key == 'down':
            if num_options > 0:
                selected_index = (selected_index + 1) % num_options
                while "---" in options[filtered_indices[selected_index]]:
                    selected_index = (selected_index + 1) % num_options
        elif key == 'space':
            if multi_select and num_options > 0:
                orig_idx = filtered_indices[selected_index]
                if "---" not in options[orig_idx]:
                    if orig_idx in selected_items: selected_items.remove(orig_idx)
                    else: selected_items.add(orig_idx)
            elif enable_search:
                search_query += " "
                selected_index = 0
        elif key == 'enter':
            print(UI.SHOW_CURSOR, end="")
            if multi_select:
                if not selected_items and num_options > 0:
                    return [i for i in filtered_indices if "---" not in options[i]]
                return list(selected_items)
            else:
                if num_options > 0:
                    orig_idx = filtered_indices[selected_index]
                    if "---" not in options[orig_idx]: return orig_idx
                return -1
        elif key == 'esc':
            if enable_search and search_query:
                search_query = ""
                selected_index = 0
            else:
                print(UI.SHOW_CURSOR, end="")
                return [] if multi_select else -1
        elif key == 'backspace':
            if enable_search:
                search_query = search_query[:-1]
                selected_index = 0
        elif key and len(key) == 1:
            if enable_search:
                search_query += key
                selected_index = 0
            else:
                if key.isdigit() or key.isalpha():
                    for orig_idx in filtered_indices:
                        opt_str = options[orig_idx].strip()
                        if opt_str.lower().startswith(f"{key.lower()}.") or opt_str.lower().startswith(f"{key.lower()} "):
                            print(UI.SHOW_CURSOR, end="")
                            return orig_idx

def get_ffprobe_info(filepath):
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{UI.HEADER}--- File Information ---{UI.END}\n")
    subprocess.run(f'ffprobe -v quiet -show_entries format=size,duration,bit_rate:stream=codec_name,width,height,r_frame_rate -of default=noprint_wrappers=1 "{filepath}"', shell=True)
    print(f"\n{UI.CYAN}Press Enter to return...{UI.END}")
    input()

def open_file_default(filepath):
    try:
        if os.name == 'nt': os.startfile(filepath)
        elif sys.platform == 'darwin': subprocess.run(['open', filepath])
        else: subprocess.run(['xdg-open', filepath])
    except: pass

def run_process_flow(commands):
    all_files = [f for f in os.listdir('.') if os.path.isfile(f)]
    files = [f for f in all_files if os.path.splitext(f)[1].lower() in Media.ALL]
    
    if not files:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{UI.RED}No media files found in the current directory!{UI.END}")
        input("\nPress Enter to return...")
        return

    menu_files = [f"{Media.get_label(f)} {f}" for f in files]
    
    subtitle = "Space: Toggle | Enter: Confirm (Hit Enter without selection = Select All Visible) | Type to search"
    sel_indices = interactive_menu("SELECT MEDIA FILES", menu_files, subtitle=subtitle, multi_select=True, enable_search=True, max_visible=11)
    
    if not sel_indices: return
    sel_files = [files[i] for i in sel_indices]

    while True:
        menu_options = [
            "1. [Manual] Enter Custom FFmpeg Command",
            "2. [Presets] Select from Saved Presets",
            "--------------------------"
        ]
        
        if len(sel_files) == 1:
            menu_options.extend([
                "3. View Media Info (ffprobe)",
                "4. Preview Media",
                "--------------------------"
            ])
            
        menu_options.append("0. Back")
        
        c_idx = interactive_menu(f"PROCESS: {len(sel_files)} file(s) selected", menu_options)
        if c_idx == -1 or "0. Back" in menu_options[c_idx]: break
        
        action = menu_options[c_idx]
        if "---" in action: continue
        
        if "View Info" in action:
            get_ffprobe_info(sel_files[0])
            continue
        elif "Preview" in action:
            open_file_default(sel_files[0])
            continue

        if "[Presets]" in action:
            cmd_names = list(commands.keys())
            if not cmd_names:
                print(f"{UI.RED}No presets found! Please add one in 'Manage Presets'.{UI.END}")
                input("Press Enter...")
                continue
            
            p_opts = cmd_names + ["--------------------------", "0. Back"]
            p_idx = interactive_menu("SELECT PRESET", p_opts)
            if p_idx == -1 or "Back" in p_opts[p_idx]: 
                continue
            preset_name = cmd_names[p_idx]
            cmd_template = commands[preset_name]["cmd"]
            output_ext = commands[preset_name]["ext"]

        elif "[Manual]" in action:
            global last_manual_cmd, last_manual_ext
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"{UI.HEADER}=== MANUAL COMMAND ==={UI.END}")
            print(f"{UI.GRAY}Enter FFmpeg arguments that come AFTER the input file (-i).{UI.END}")
            print(f"{UI.GRAY}Example: -c:v libx264 -crf 23 -c:a aac{UI.END}")
            print(f"{UI.CYAN}(Esc or type 'exit' to cancel){UI.END}\n")
            
            prompt1 = f"{UI.BOLD}Arguments > {UI.END}"
            cmd_template = interactive_input(prompt1, last_manual_cmd)
            if cmd_template is None or cmd_template.strip().lower() == 'exit': continue
            
            print()
            prompt2 = f"{UI.BOLD}Output extension{UI.END} {UI.GRAY}(e.g. .mp4) [Leave blank to keep original]:{UI.END} "
            output_ext = interactive_input(prompt2, last_manual_ext if last_manual_ext else ".")
            if output_ext is None: continue
            
            cmd_template = cmd_template.strip()
            output_ext = output_ext.strip()
            last_manual_cmd = cmd_template
            last_manual_ext = output_ext
        
        post_opts = ["1. Keep original files (Safe)", "2. Delete original files after SUCCESS", "0. Back"]
        post_idx = interactive_menu("POST-PROCESS ACTION", post_opts)
        if post_idx == -1 or post_opts[post_idx] == "0. Back": continue
        delete_after = ("Delete" in post_opts[post_idx])

        if len(sel_files) > 1:
            thread_opts = ["1. Sequential (1 process at a time)", "2. Run 2 processes concurrently", "3. Run 3 processes concurrently", "4. Run 4 processes concurrently", "--------------------------", "0. Back"]
            t_choice = interactive_menu("CONCURRENCY LEVEL", thread_opts)
            if t_choice == -1 or "Back" in thread_opts[t_choice] or "---" in thread_opts[t_choice]: continue
            max_workers = t_choice + 1
        else:
            max_workers = 1

        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{UI.HEADER}=== PROCESSING {len(sel_files)} FILE(S) ({max_workers} THREADS) ==={UI.END}\n")
        if max_workers > 1: print(f"{UI.CYAN}Spawning FFmpeg windows. Please wait...{UI.END}\n")
        
        success_count = 0
        fail_count = 0
        
        import concurrent.futures
        
        active_processes = []
        cancel_requested = [False]

        def worker(input_file):
            if cancel_requested[0]:
                return False, input_file, "Cancelled"
                
            filename, old_ext = os.path.splitext(input_file)
            cur_out_ext = output_ext if output_ext else old_ext
            if cur_out_ext and not cur_out_ext.startswith('.'): cur_out_ext = '.' + cur_out_ext
            
            output_file = f"{filename}_output{cur_out_ext}"
            
            if os.name == 'nt':
                final_cmd = f'ffmpeg -y -i "{input_file}" {cmd_template} "{output_file}"'
                creationflags = getattr(subprocess, 'CREATE_NEW_CONSOLE', 0x00000010)
                p = subprocess.Popen(final_cmd, shell=False, creationflags=creationflags)
            else:
                final_cmd = f'ffmpeg -y -i "{input_file}" {cmd_template} "{output_file}"'
                p = subprocess.Popen(final_cmd, shell=True)
                
            active_processes.append(p)
            p.wait()
            try: active_processes.remove(p)
            except: pass
            
            success = (p.returncode == 0)
            
            if success and delete_after:
                try: os.remove(input_file)
                except Exception: pass
                
            return success, input_file, output_file

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(worker, f): f for f in sel_files}
                for future in concurrent.futures.as_completed(futures):
                    success, in_f, out_f = future.result()
                    if out_f == "Cancelled":
                        continue
                    if success:
                        success_count += 1
                        msg = f" {UI.GREEN}✓{UI.END} {in_f} -> {UI.YELLOW}{out_f}{UI.END}"
                        if delete_after: msg += f" {UI.GRAY}(Deleted original){UI.END}"
                        print(msg)
                    else:
                        fail_count += 1
                        print(f" {UI.RED}✗ Failed:{UI.END} {in_f}")
                        
            print(f"\n{UI.HEADER}=== COMPLETED ==={UI.END}")
            print(f"Processed successfully: {UI.GREEN}{success_count}{UI.END} file(s).")
            if fail_count > 0:
                print(f"Failed: {UI.RED}{fail_count}{UI.END} file(s).")
                
        except KeyboardInterrupt:
            cancel_requested[0] = True
            print(f"\n{UI.RED}Process Cancelled by User (Ctrl+C)! Killing ffmpeg tasks...{UI.END}")
            for p in active_processes:
                try: p.kill()
                except: pass
            print(f"{UI.RED}Batch process aborted.{UI.END}")
            
        input("\nPress Enter to return to main menu...")
        break

def manage_commands(commands):
    while True:
        opts = ["1. List saved commands", "2. Add new command", "3. Edit saved command", "4. Delete saved command", "--------------------------", "0. Back"]
        choice = interactive_menu("COMMAND MANAGEMENT", opts)
        
        if choice == 0:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"{UI.HEADER}{UI.BOLD}=== SAVED PRESETS ==={UI.END}\n")
            if not commands:
                print(f" {UI.GRAY}No presets found.{UI.END}")
            else:
                max_name_len = max(len(k) for k in commands.keys()) if commands else 10
                for k, v in commands.items(): 
                    name = f"{UI.CYAN}{UI.BOLD}{k.ljust(max_name_len)}{UI.END}"
                    ext  = f"{UI.YELLOW}{v['ext'].rjust(6)}{UI.END}"
                    cmd  = f"{UI.GRAY}{v['cmd']}{UI.END}"
                    print(f" {name} {UI.GRAY}|{UI.END} {ext} {UI.GRAY}|{UI.END} {cmd}")
            input("\nPress Enter to return...")
            
        elif choice == 1 or choice == 2:
            is_edit = (choice == 2)
            old_name = ""
            data = {"cmd": "", "ext": ".mp4"}
            
            if is_edit:
                names = list(commands.keys())
                if not names:
                    print(f"{UI.RED}No presets to edit!{UI.END}")
                    input("Press Enter...")
                    continue
                e_idx = interactive_menu("SELECT PRESET TO EDIT", names)
                if e_idx == -1: continue
                old_name = names[e_idx]
                data = commands[old_name]

            fields = [
                ("name", "Name", old_name if is_edit else "New Preset"),
                ("cmd",  "Options", data["cmd"]),
                ("ext",  "Extension", data["ext"])
            ]
            
            new_values = {}
            cancelled = False
            
            for i, (key, label, current_val) in enumerate(fields):
                os.system('cls' if os.name == 'nt' else 'clear')
                title = "EDIT PRESET" if is_edit else "ADD NEW PRESET"
                print(f"{UI.HEADER}{UI.BOLD}=== {title} ==={UI.END}")
                print(f"{UI.CYAN}(Type 'exit' to cancel, Enter to keep/default){UI.END}\n")
                
                col_w = 20
                col_c = 45
                print(f" {UI.GRAY}{'FIELD'.ljust(col_w)} | {'CURRENT'.ljust(col_c)} | {'NEW VALUE'}{UI.END}")
                print(f" {UI.GRAY}{'-'*col_w}-+-{'-'*col_c}-+-{'-'*25}{UI.END}")
                
                for j, (f_key, f_label, f_curr) in enumerate(fields):
                    disp_curr = (f_curr[:42] + '..') if len(str(f_curr)) > 44 else str(f_curr)
                    
                    if i == j:
                        prompt_str = f" {UI.BOLD}{UI.YELLOW}➜ {f_label.ljust(col_w-2)}{UI.END} | {UI.WHITE}{disp_curr.ljust(col_c)}{UI.END} | "
                        
                        if f_key == "ext" and not f_curr: f_curr = "."
                        
                        val = interactive_input(prompt_str, f_curr if is_edit else ("." if f_key == "ext" else ""))
                        if val is None or val.strip().lower() == 'exit':
                            cancelled = True
                            break
                        new_values[f_key] = val.strip() if val.strip() else (f_curr if is_edit else "")
                    else:
                        val_done = new_values.get(f_key, "...")
                        print(f" {UI.GRAY}  {f_label.ljust(col_w-2)} | {disp_curr.ljust(col_c)} | {val_done}{UI.END}")
                
                if cancelled: break
            
            if not cancelled:
                final_name = new_values["name"] or old_name
                if final_name:
                    if is_edit and final_name != old_name:
                        del commands[old_name]
                    
                    ext = new_values["ext"]
                    if ext and not ext.startswith('.'): ext = '.' + ext
                    
                    commands[final_name] = {"cmd": new_values["cmd"], "ext": ext or ".mp4"}
                    save_commands(commands)
        
        elif choice == 3:
            names = list(commands.keys())
            if not names:
                print(f"{UI.RED}No presets to delete!{UI.END}")
                input("Press Enter...")
                continue
            
            max_name_len = max(len(k) for k in names)
            menu_options = []
            for k in names:
                v = commands[k]
                line = f"{k.ljust(max_name_len)} | {v['ext'].rjust(5)} | {v['cmd'][:80]}..." if len(v['cmd']) > 80 else f"{k.ljust(max_name_len)} | {v['ext'].rjust(5)} | {v['cmd']}"
                menu_options.append(line)
            
            d_idx = interactive_menu("SELECT PRESET TO DELETE", menu_options)
            if d_idx != -1:
                target_name = names[d_idx]
                confirm = interactive_menu(f"CONFIRM DELETE: {target_name}?", ["1. No, Cancel", "2. Yes, Delete It"])
                if confirm == 1:
                    del commands[target_name]
                    save_commands(commands)
        else: break

def main():
    commands = load_commands()
    while True:
        choice = interactive_menu("FFmpeg Tool (by Natelyt)", [
            "1. Process Media", 
            "2. Manage Presets", 
            "--------------------------", 
            "0. Exit"
        ])
        if choice == 0: run_process_flow(commands)
        elif choice == 1: manage_commands(commands)
        elif choice == 3 or choice == -1: 
            print(UI.SHOW_CURSOR, end="")
            os.system('cls' if os.name == 'nt' else 'clear')
            os._exit(0) # Buộc đóng terminal process

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(UI.SHOW_CURSOR)
        os._exit(0)
