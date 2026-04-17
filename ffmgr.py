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
    """Chỉ dùng để điều hướng menu bằng phím mũi tên"""
    if os.name == 'nt':
        import msvcrt
        key = msvcrt.getch()
        if key in (b'\x00', b'\xe0'):
            key = msvcrt.getch()
            return {'H': 'up', 'P': 'down'}.get(key.decode(), None)
        if key == b'\r': return 'enter'
        if key == b'\x1b': return 'esc'
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
                    return {'[A': 'up', '[B': 'down'}.get(ch2, None)
                return 'esc'
            if ch == '\r': return 'enter'
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return None

def interactive_menu(title, options, subtitle=None, max_visible=None):
    selected_index = 0
    num_options = len(options)
    limit = max_visible if max_visible is not None else max(num_options, 1)
    os.system('cls' if os.name == 'nt' else 'clear')
    print(UI.HIDE_CURSOR, end="")
    try:
        while True:
            print(UI.HOME_CURSOR, end="") 
            print(f"{UI.HEADER}{UI.BOLD}=== {title} ==={UI.END}\033[K")
            if subtitle: print(f" {UI.GRAY}{subtitle}{UI.END}\033[K")
            
            start_index = max(0, selected_index - limit // 2)
            end_index = start_index + limit
            if end_index > num_options:
                end_index = num_options
                start_index = max(0, end_index - limit)
                
            if start_index > 0:
                print(f"    {UI.CYAN}▲{UI.END}\033[K")
            else:
                print("\033[K") # Dòng trắng thay cho khoảng trống của mũi tên
                
            for i in range(start_index, end_index):
                option = options[i]
                print('\033[K', end="") # Xóa dòng hiện tại
                if "---" in option:
                    print(f" {UI.GRAY} {option}{UI.END}")
                    continue
                
                disp_option = option
                if i == selected_index:
                    if UI.END in disp_option:
                        disp_option = disp_option.replace(UI.END, UI.END + UI.SELECT)
                    print(f" {UI.SELECT}➜  {disp_option}{UI.END}")
                else:
                    if UI.END in disp_option:
                        disp_option = disp_option.replace(UI.END, UI.END + UI.WHITE)
                    print(f"    {UI.WHITE}{disp_option}{UI.END}")
                    
            if end_index < num_options:
                print(f"    {UI.CYAN}▼{UI.END}\033[K")
            else:
                print("\033[K")
                
            scroll_info = f" | Showing {start_index+1}-{end_index} of {num_options}" if limit < num_options else ""
            print(f"{UI.CYAN}(Arrows: Move, Enter: Select, Esc: Back){scroll_info}{UI.END}\033[K")
            print('\033[J', end="") # Xoá các dòng cũ bên dưới
            key = get_key()
            if key == 'up':
                selected_index = (selected_index - 1) % num_options
                if "---" in options[selected_index]: selected_index = (selected_index - 1) % num_options
            elif key == 'down':
                selected_index = (selected_index + 1) % num_options
                if "---" in options[selected_index]: selected_index = (selected_index + 1) % num_options
            elif key == 'enter':
                print(UI.SHOW_CURSOR, end="")
                return selected_index
            elif key == 'esc':
                print(UI.SHOW_CURSOR, end="")
                return -1
    except Exception:
        print(UI.SHOW_CURSOR, end="")
        return -1

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

def run_ffmpeg_flow(commands):
    # Quét và lọc file media
    all_files = [f for f in os.listdir('.') if os.path.isfile(f)]
    files = [f for f in all_files if os.path.splitext(f)[1].lower() in Media.ALL]
    
    if not files:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{UI.RED}No media files found in the current directory!{UI.END}")
        print(f"{UI.GRAY}Only Video, Audio, and Image files are supported.{UI.END}")
        input("\nPress Enter to return...")
        return

    # Tạo menu với nhãn phân loại
    menu_files = [f"{Media.get_label(f)} {f}" for f in files]
    
    cwd = os.getcwd()
    f_idx = interactive_menu("SELECT INPUT FILE", menu_files, subtitle=f"Scanning media in: {cwd}", max_visible=11)
    if f_idx == -1: return
    input_file = files[f_idx]

    while True:
        menu_options = [
            "[Manual] Enter Custom Command",
            "[Presets] Select Preset",
            "--------------------------",
            "View Info (ffprobe)",
            "Preview",
            "Delete File",
            "--------------------------",
            "Back"
        ]
        c_idx = interactive_menu(f"PROCESS: {input_file}", menu_options)
        
        if c_idx == -1 or menu_options[c_idx] == "Back": break
        
        action = menu_options[c_idx]
        
        if action == "[Presets] Select Preset":
            cmd_names = list(commands.keys())
            if not cmd_names:
                print(f"{UI.RED}No presets found!{UI.END}")
                input("Press Enter...")
                continue
            
            p_opts = cmd_names + ["--------------------------", "Back"]
            p_idx = interactive_menu("SELECT PRESET", p_opts)
            if p_idx == -1 or p_opts[p_idx] == "Back": 
                continue
            action = cmd_names[p_idx]

        if action == "View Info (ffprobe)":
            get_ffprobe_info(input_file)
            continue
        elif action == "Preview":
            open_file_default(input_file)
            continue
        elif action == "Delete File":
            confirm = interactive_menu(f"DELETE PERMANENTLY: {input_file}?", ["No", "Yes, Delete"])
            if confirm == 1:
                os.remove(input_file)
                return
            continue
        elif "---" in action: continue

        # Xử lý nhập Command
        if action == "[Manual] Enter Custom Command":
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"{UI.YELLOW}Enter FFmpeg options (after -i input):{UI.END}")
            print(f"{UI.CYAN}(Type 'exit' to go back){UI.END}")
            cmd_template = input(f"{UI.BOLD}> {UI.END}").strip()
            if cmd_template.lower() == 'exit': continue
            
            output_ext = input(f"{UI.YELLOW}Output extension (include dot, e.g. .mp4):{UI.END} ").strip()
            if not output_ext: output_ext = os.path.splitext(input_file)[1]
        else:
            cmd_template = commands[action]["cmd"]
            output_ext = commands[action]["ext"]
            
            # Hỏi xem có muốn xóa file sau khi chạy không
            post_action = interactive_menu(f"PRESET: {action}", ["Run only", "Run then delete input file", "Back"])
            if post_action == -1 or post_action == 2: continue
            delete_after = (post_action == 1)

        filename, old_ext = os.path.splitext(input_file)
        # Nếu output_ext không bắt đầu bằng dấu chấm, thêm nó vào
        if output_ext and not output_ext.startswith('.'): output_ext = '.' + output_ext
        
        output_file = f"{filename}_output{output_ext}"
        os.system('cls' if os.name == 'nt' else 'clear')
        final_cmd = f'ffmpeg -i "{input_file}" {cmd_template} "{output_file}"'
        print(f"{UI.BLUE}Executing:{UI.END} {UI.YELLOW}{final_cmd}{UI.END}\n")
        
        result = subprocess.run(final_cmd, shell=True)
        if result.returncode == 0:
            print(f"\n{UI.GREEN}Success! Output: {output_file}{UI.END}")
            if action != "[Manual] Enter Custom Command" and delete_after:
                try:
                    os.remove(input_file)
                    print(f"{UI.RED}Deleted input file: {input_file}{UI.END}")
                except Exception as e:
                    print(f"{UI.RED}Error deleting file: {e}{UI.END}")
        else:
            print(f"\n{UI.RED}FFmpeg failed with return code {result.returncode}{UI.END}")
            
        input("Press Enter...")
        break

def run_batch_flow(commands):
    all_files = [f for f in os.listdir('.') if os.path.isfile(f)]
    video_files = [f for f in all_files if os.path.splitext(f)[1].lower() in Media.VIDEO]
    audio_files = [f for f in all_files if os.path.splitext(f)[1].lower() in Media.AUDIO]
    image_files = [f for f in all_files if os.path.splitext(f)[1].lower() in Media.IMAGE]

    types_menu = []
    types_map = []
    if video_files:
        types_menu.append(f"{UI.CYAN}[VIDEO] {len(video_files)} files{UI.END}")
        types_map.append(("VIDEO", video_files))
    if audio_files:
        types_menu.append(f"{UI.GREEN}[AUDIO] {len(audio_files)} files{UI.END}")
        types_map.append(("AUDIO", audio_files))
    if image_files:
        types_menu.append(f"{UI.YELLOW}[IMAGE] {len(image_files)} files{UI.END}")
        types_map.append(("IMAGE", image_files))
        
    if not types_menu:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{UI.RED}No media files found to batch process!{UI.END}")
        input("\nPress Enter to return...")
        return
        
    types_menu.extend(["--------------------------", "Back"])
    types_map.extend([(None, None), (None, None)])
        
    t_idx = interactive_menu("SELECT MEDIA TYPE FOR BATCH PROCESS", types_menu)
    if t_idx == -1 or types_menu[t_idx] == "Back" or "---" in types_menu[t_idx]: 
        return
        
    sel_type, sel_files = types_map[t_idx]
    
    while True:
        menu_options = [
            "[Manual] Enter Custom Command",
            "[Presets] Select Preset",
            "--------------------------",
            "Back"
        ]
        c_idx = interactive_menu(f"BATCH PROCESS: {len(sel_files)} {sel_type} files", menu_options)
        
        if c_idx == -1 or menu_options[c_idx] == "Back": break
        
        action = menu_options[c_idx]
        if "---" in action: continue
        
        if action == "[Presets] Select Preset":
            cmd_names = list(commands.keys())
            if not cmd_names:
                print(f"{UI.RED}No presets found!{UI.END}")
                input("Press Enter...")
                continue
            
            p_opts = cmd_names + ["--------------------------", "Back"]
            p_idx = interactive_menu("SELECT PRESET FOR BATCH", p_opts)
            if p_idx == -1 or p_opts[p_idx] == "Back": 
                continue
            action = cmd_names[p_idx]

        if action == "[Manual] Enter Custom Command":
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"{UI.YELLOW}Enter FFmpeg options (after -i input):{UI.END}")
            print(f"{UI.CYAN}(Type 'exit' to go back){UI.END}")
            cmd_template = input(f"{UI.BOLD}> {UI.END}").strip()
            if cmd_template.lower() == 'exit': continue
            
            output_ext = input(f"{UI.YELLOW}Output extension (include dot, e.g. .mp4):{UI.END} ").strip()
            post_action = interactive_menu(f"BATCH PROCESS", ["Run only", "Run then delete input files", "Back"])
            if post_action == -1 or post_action == 2: continue
            delete_after = (post_action == 1)
        else:
            cmd_template = commands[action]["cmd"]
            output_ext = commands[action]["ext"]
            
            post_action = interactive_menu(f"PRESET: {action} (BATCH)", ["Run only", "Run then delete input files", "Back"])
            if post_action == -1 or post_action == 2: continue
            delete_after = (post_action == 1)

        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{UI.HEADER}=== STARTING BATCH PROCESS ==={UI.END}\n")
        
        success_count = 0
        fail_count = 0
        
        for input_file in sel_files:
            filename, old_ext = os.path.splitext(input_file)
            cur_out_ext = output_ext if output_ext else old_ext
            if cur_out_ext and not cur_out_ext.startswith('.'): cur_out_ext = '.' + cur_out_ext
            
            output_file = f"{filename}_output{cur_out_ext}"
            final_cmd = f'ffmpeg -i "{input_file}" {cmd_template} "{output_file}"'
            
            print(f"\n{UI.BLUE}Processing:{UI.END} {input_file} -> {UI.YELLOW}{output_file}{UI.END}")
            result = subprocess.run(final_cmd, shell=True)
            if result.returncode == 0:
                success_count += 1
                if delete_after:
                    try:
                        os.remove(input_file)
                        print(f" {UI.GRAY}Deleted: {input_file}{UI.END}")
                    except Exception: pass
            else:
                fail_count += 1
                print(f" {UI.RED}Failed to process: {input_file}{UI.END}")
        
        print(f"\n{UI.HEADER}=== BATCH COMPLETED ==={UI.END}")
        print(f"Processed successfully: {UI.GREEN}{success_count}{UI.END} file(s).")
        if fail_count > 0:
            print(f"Failed: {UI.RED}{fail_count}{UI.END} file(s).")
            
        input("\nPress Enter to return...")
        break

def manage_commands(commands):
    while True:
        opts = ["List saved commands", "Add new command", "Edit saved command", "Delete saved command", "--------------------------", "Back"]
        choice = interactive_menu("COMMAND MANAGEMENT", opts)
        
        if choice == 0:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"{UI.HEADER}{UI.BOLD}=== SAVED PRESETS ==={UI.END}\n")
            if not commands:
                print(f" {UI.GRAY}No presets found.{UI.END}")
            else:
                # Tìm độ dài tên dài nhất để căn lề
                max_name_len = max(len(k) for k in commands.keys()) if commands else 10
                for k, v in commands.items(): 
                    name = f"{UI.CYAN}{UI.BOLD}{k.ljust(max_name_len)}{UI.END}"
                    ext  = f"{UI.YELLOW}{v['ext'].rjust(6)}{UI.END}"
                    cmd  = f"{UI.GRAY}{v['cmd']}{UI.END}"
                    print(f" {name} {UI.GRAY}|{UI.END} {ext} {UI.GRAY}|{UI.END} {cmd}")
            input("\nPress Enter to return...")
            
        elif choice == 1 or choice == 2: # Add (1) or Edit (2)
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

            # Form fields definition
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
                
                # Header
                col_w = 20
                col_c = 45
                print(f" {UI.GRAY}{'FIELD'.ljust(col_w)} | {'CURRENT'.ljust(col_c)} | {'NEW VALUE'}{UI.END}")
                print(f" {UI.GRAY}{'-'*col_w}-+-{'-'*col_c}-+-{'-'*25}{UI.END}")
                
                # Draw rows
                for j, (f_key, f_label, f_curr) in enumerate(fields):
                    disp_curr = (f_curr[:42] + '..') if len(str(f_curr)) > 44 else str(f_curr)
                    
                    if i == j: # Active field
                        print(f" {UI.BOLD}{UI.YELLOW}➜ {f_label.ljust(col_w-2)}{UI.END} | {UI.WHITE}{disp_curr.ljust(col_c)}{UI.END} | ", end="")
                        val = input().strip()
                        if val.lower() == 'exit':
                            cancelled = True
                            break
                        new_values[f_key] = val if val else (f_curr if is_edit else ("" if f_key == "name" else f_curr))
                    else: # Inactive field
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
        
        elif choice == 3: # Delete
            names = list(commands.keys())
            if not names:
                print(f"{UI.RED}No presets to delete!{UI.END}")
                input("Press Enter...")
                continue
            
            # Format menu options similar to List view
            max_name_len = max(len(k) for k in names)
            menu_options = []
            for k in names:
                v = commands[k]
                # Format: Name | Ext | Cmd (không dùng màu bên trong vì menu sẽ tô màu cả dòng)
                line = f"{k.ljust(max_name_len)} | {v['ext'].rjust(5)} | {v['cmd'][:80]}..." if len(v['cmd']) > 80 else f"{k.ljust(max_name_len)} | {v['ext'].rjust(5)} | {v['cmd']}"
                menu_options.append(line)
            
            d_idx = interactive_menu("SELECT PRESET TO DELETE", menu_options)
            if d_idx != -1:
                target_name = names[d_idx]
                confirm = interactive_menu(f"CONFIRM DELETE: {target_name}?", ["No, Cancel", "Yes, Delete It"])
                if confirm == 1:
                    del commands[target_name]
                    save_commands(commands)
        else: break

def main():
    commands = load_commands()
    while True:
        choice = interactive_menu("FFmpeg Tool (by Natelyt)", ["Single File", "Batch Process", "Manage Presets", "--------------------------", "Exit"])
        if choice == 0: run_ffmpeg_flow(commands)
        elif choice == 1: run_batch_flow(commands)
        elif choice == 2: manage_commands(commands)
        elif choice == 4 or choice == -1: 
            print(UI.SHOW_CURSOR, end="")
            os.system('cls' if os.name == 'nt' else 'clear')
            os._exit(0) # Buộc đóng terminal process

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(UI.SHOW_CURSOR)
        os._exit(0)
