#!/usr/bin/env python3
import pypresence
import json
import time
import os
import sys
import signal
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

CLIENT_ID = "1409915140484104364" 

JSON_FILE = "./tekken8_discord_rpc.json"

GAME_MODE_INFO = {
    "main_menu": {"details": "TEKKEN 8", "state": "Main Menu", "large_image": "tekken8_logo"},
    "character_select": {"details": "TEKKEN 8", "state": "Selecting Character", "large_image": "character_select"},
    "stage_select": {"details": "TEKKEN 8", "state": "Selecting Stage", "large_image": "stage_select"},
    "side_select": {"details": "TEKKEN 8", "state": "Selecting Side", "large_image": "tekken8_logo"},
    "session_room": {"details": "Player Match", "state": "In Session Room", "large_image": "player_match"},
    "loading": {"details": "TEKKEN 8", "state": "Loading...", "large_image": "loading"},
    "practice": {"details": "Practice Mode", "state": "Training", "large_image": "practice_mode"},
    "battle": {"details": "Fighting", "state": "In Battle", "large_image": "battle"},
    "result": {"details": "TEKKEN 8", "state": "Match Results", "large_image": "results"},
    "startup": {"details": "TEKKEN 8", "state": "Starting Game", "large_image": "tekken8_logo"},
    "game_closed": {"details": "TEKKEN 8", "state": "Game Closed", "large_image": "tekken8_logo"},
    "menu": {"details": "TEKKEN 8", "state": "In Menus", "large_image": "tekken8_logo"}
}

# 한글버전
# GAME_MODE_INFO = {
#     "main_menu": {"details": "철권 8", "state": "메인 메뉴", "large_image": "tekken8_logo"},
#     "character_select": {"details": "철권 8", "state": "캐릭터 선택중... ", "large_image": "character_select"},
#     "stage_select": {"details": "철권 8", "state": "스테이지 선택중...", "large_image": "stage_select"},
#     "side_select": {"details": "철권 8", "state": "플레이 사이드 선택중... ", "large_image": "tekken8_logo"},
#     "session_room": {"details": "철권 8 ", "state": "플레이어 매치 대기중...", "large_image": "player_match"},
#     "loading": {"details": "철권 8", "state": "로딩중...", "large_image": "loading"},
#     "practice": {"details": "철권 8", "state": "연습 모드", "large_image": "practice_mode"},
#     "battle": {"details": "철권 8", "state": "배틀중...", "large_image": "battle"},
#     "result": {"details": "철권 8", "state": "매치 결과", "large_image": "results"},
#     "startup": {"details": "철권 8", "state": "게임 시작중...", "large_image": "tekken8_logo"},
#     "game_closed": {"details": "철권 8", "state": "게임 꺼짐", "large_image": "tekken8_logo"},
#     "menu": {"details": "철권 8", "state": "메뉴", "large_image": "tekken8_logo"}
# }

# 디코용 이미지 매핑
CHARACTER_IMAGES = {
    "Jin": "jin",
    "Kazuya": "kazuya",
    "Jun": "jun", 
    "Paul": "paul",
    "King": "king",
    "Lars": "lars",
    "Nina": "nina",
    "Jack-8": "jack8",
    "Law": "law",
    "Raven": "raven",
    "Dragunov": "dragunov",
    "Leo": "leo",
    "Steve": "steve",
    "Yoshimitsu": "yoshimitsu", 
    "Hwoarang": "hwoarang",
    "Bryan": "bryan",
    "Claudio": "claudio",
    "Azucena": "azucena",
    "Lili": "lili",
    "Asuka": "asuka",
    "Feng": "feng",
    "Leroy": "leroy",
    "Alisa": "alisa",
    "Xiaoyu": "xiaoyu",
    "Zafina": "zafina",
    "Victor": "victor",
    "Reina": "reina",
    "Kuma": "kuma",
    "Panda": "panda", 
    "Shaheen": "shaheen",
    "Lee": "lee",
    "Devil Jin": "devil_jin",
    "Eddy": "eddy",
    "Lidia": "lidia",
    "Heihachi": "heihachi",
    "Clive": "clive",
    "Anna": "anna",
    "Fahkumram": "fahkumram",
    "Armor King": "armorking"
}


class JSONFileHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback
        
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(JSON_FILE):
            self.callback()
            
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(JSON_FILE):
            self.callback()

class TekkenDiscordRPC:
    def __init__(self):
        self.rpc = None
        self.connected = False
        self.last_state = None
        self.connection_attempts = 0
        self.max_connection_attempts = 5
        self.should_exit = False
        self.file_observer = None
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        print("\nShutdown signal received...")
        self.should_exit = True
        self.cleanup()
        
    def connect_discord(self):
        try:
            self.rpc = pypresence.Presence(CLIENT_ID)
            self.rpc.connect()
            self.connected = True
            self.connection_attempts = 0
            return True
        except Exception as e:
            self.connected = False
            self.connection_attempts += 1
            if self.connection_attempts <= 3:  # 처음 3번까지만 에러 메시지 표시
                print(f"Discord connection failed (attempt {self.connection_attempts}): {e}")
            return False
    
    def read_game_state(self):
        try:
            if not os.path.exists(JSON_FILE):
                return None
                
            if os.path.getsize(JSON_FILE) == 0:
                return None
                
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                if data.get('game_mode') == 'game_closed':
                    print("Game closed detected")
                    self.should_exit = True
                    return None
                    
                return data
        except (json.JSONDecodeError, FileNotFoundError, PermissionError):
            return None
    
    def get_character_image(self, character_name):
        return CHARACTER_IMAGES.get(character_name, "tekken8_logo")
    
    def format_vs_display(self, p1_char, p2_char):
        if p1_char != "unknown" and p2_char != "unknown":
            return f"{p1_char} VS {p2_char}"
        elif p1_char != "unknown":
            return f"Playing as {p1_char}"
        else:
            return "Fighting"
    
    # 한글버전
    # def format_vs_display(self, p1_char, p2_char):
    #     if p1_char != "unknown" and p2_char != "unknown":
    #         return f"{p1_char} VS {p2_char}"
    #     elif p1_char != "unknown":
    #         return f"{p1_char} 플레이 중..."
    #     else:
    #         return "배틀중..."
    
    def update_discord_presence(self, state):
        if not self.connected:
            return False
            
        try:
            game_mode = state.get('game_mode', 'menu')
            p1_char = state.get('p1_character', 'unknown')
            p2_char = state.get('p2_character', 'unknown')
            timestamp = state.get('timestamp', int(time.time()))
            
            mode_info = GAME_MODE_INFO.get(game_mode, GAME_MODE_INFO['menu'])
            
            details = mode_info['details']
            state_text = mode_info['state']
            large_image = mode_info['large_image']
            small_image = "tekken8_logo"
            small_text = "Tekken 8"
            
            if game_mode in ['battle', 'practice']:
                if p1_char != "unknown":
                    details = self.format_vs_display(p1_char, p2_char)
                    small_image = self.get_character_image(p1_char)
                    small_text = p1_char
                    
                    if game_mode == 'practice':
                        state_text = f"Training with {p1_char}"
            
            # 한글버전
            # if game_mode in ['battle', 'practice']:
            #     if p1_char != "unknown":
            #         details = self.format_vs_display(p1_char, p2_char)
            #         small_image = self.get_character_image(p1_char)
            #         small_text = p1_char
                    
            #         if game_mode == 'practice':
            #             state_text = f"{p1_char} 연습하는 중..."
            
            elif game_mode == 'loading':
                if p1_char != "unknown":
                    details = self.format_vs_display(p1_char, p2_char)
                    small_image = self.get_character_image(p1_char)
                    small_text = p1_char
            
            # Discord 업데이트 실행
            self.rpc.update(
                details=details,
                state=state_text,
                large_image=large_image,
                large_text="Tekken 8",
                small_image=small_image,
                small_text=small_text,
                start=timestamp
            )
            
            print(f"Discord Updated: {details} | {state_text}")
            return True
            
        except Exception as e:
            print(f"Discord update failed: {e}")
            self.connected = False
            return False
    
    def wait_for_json_file(self):
        print(f"Waiting for {JSON_FILE} to be created...")
        
        event_handler = JSONFileHandler(self.on_file_created)
        self.file_observer = Observer()
        self.file_observer.schedule(event_handler, ".", recursive=False)
        self.file_observer.start()
        
        try:
            while not os.path.exists(JSON_FILE) and not self.should_exit:
                time.sleep(1)
        finally:
            if self.file_observer:
                self.file_observer.stop()
                self.file_observer.join()
                
        if os.path.exists(JSON_FILE):
            print(f"{JSON_FILE} detected! Starting RPC...")
            return True
        return False
    
    def on_file_created(self):
        if os.path.exists(JSON_FILE):
            print(f"{JSON_FILE} created!")
    
    def detect_game_process(self):
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and 'Polaris-Win64-Shipping.exe' in proc.info['name']:
                    return True
        except ImportError:
            # psutil이 없으면 파일 기반으로만 체크
            pass
        except:
            # 다른 에러는 무시
            pass
        return False
    
    def monitor_game_process(self):
        game_running = self.detect_game_process()
        
        if not game_running and self.last_state:
            # 게임이 종료되었고 이전 상태가 있었다면
            print("Game process not detected - clearing Discord presence")
            if self.rpc and self.connected:
                try:
                    self.rpc.clear()
                except:
                    pass
            
            # JSON 파일 삭제
            try:
                if os.path.exists(JSON_FILE):
                    os.remove(JSON_FILE)
                    print(f"Deleted {JSON_FILE}")
            except:
                pass
                
            self.last_state = None
            
            # 3초 후 자동 종료
            print("Shutting down in 3 seconds...")
            for i in range(3, 0, -1):
                print(f"{i}...")
                time.sleep(1)
            print("Goodbye!")
            self.should_exit = True
            return False
        
        return True
    
    def cleanup(self):
        if self.file_observer and self.file_observer.is_alive():
            self.file_observer.stop()
            self.file_observer.join()
            
        if self.rpc and self.connected:
            try:
                self.rpc.clear()
                self.rpc.close()
            except:
                pass
        print("Discord RPC disconnected.")
    
    def run(self):
        print("Tekken 8 Discord RPC Client")
        print("=" * 25)
        
        # JSON 파일이 없으면 대기
        if not os.path.exists(JSON_FILE):
            if not self.wait_for_json_file():
                return
        
        print("Starting Discord RPC monitoring...")
        
        try:
            consecutive_no_data = 0
            while not self.should_exit:
                if not self.connected:
                    if not self.connect_discord():
                        time.sleep(5)
                        continue
                
                # 게임 프로세스 체크
                if consecutive_no_data % 3 == 0:
                    if not self.monitor_game_process():
                        consecutive_no_data = 0
                        continue
                
                current_state = self.read_game_state()
                
                if current_state is None:
                    consecutive_no_data += 1
                    # 10번 연속으로 데이터가 없으면 (20초) 메시지 표시
                    if consecutive_no_data == 10:
                        print("No game data for 20 seconds...")
                    elif consecutive_no_data >= 30:  # 60초 이상 데이터 없음
                        print("Long period without data - checking if game is still running...")
                        if not self.monitor_game_process():
                            break
                        consecutive_no_data = 25  # 리셋하지만 계속 체크
                else:
                    consecutive_no_data = 0
                    # 상태가 변경된 경우만 업데이트
                    if current_state != self.last_state:
                        success = self.update_discord_presence(current_state)
                        if success:
                            self.last_state = current_state
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            self.should_exit = True
        finally:
            self.cleanup()

def check_requirements():
    try:
        import pypresence
        from watchdog.observers import Observer
    except ImportError as e:
        missing = str(e).split("'")[1]
        print(f"Required library not found: {missing}")
        if missing == "pypresence":
            print("Install with: pip install pypresence")
        elif missing == "watchdog":
            print("Install with: pip install watchdog")
        return False
    
    try:
        import psutil
        print("psutil detected - game process monitoring enabled")
    except ImportError:
        print("psutil not found - install with 'pip install psutil' for better game detection")
    
    return True

def main():
    if not check_requirements():
        input("Press Enter to exit...")
        return
    
    client = TekkenDiscordRPC()
    try:
        client.run()
    except Exception as e:
        print(f"Unexpected error: {e}")
        client.cleanup()

if __name__ == "__main__":
    main()