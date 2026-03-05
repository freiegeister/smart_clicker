"""
游戏配置管理器
支持从外部目录加载游戏配置，便于打包和管理
"""
import os
import json
import shutil

class GameManager:
    def __init__(self, external_games_dir=None):
        """
        初始化游戏管理器
        
        Args:
            external_games_dir: 外部游戏目录路径（可选）
                               如果不指定，使用当前目录下的 games/
        """
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 外部游戏目录（用于开发和管理多个游戏）
        if external_games_dir and os.path.exists(external_games_dir):
            self.external_games_dir = external_games_dir
        else:
            self.external_games_dir = os.path.join(self.base_dir, "games")
        
        # 当前游戏目录（打包时使用）
        self.current_game_dir = os.path.join(self.base_dir, "current_game")
        
        # 确保目录存在
        os.makedirs(self.external_games_dir, exist_ok=True)
        os.makedirs(self.current_game_dir, exist_ok=True)
    
    def list_games(self):
        """列出所有可用的游戏"""
        games = []
        
        # 扫描外部游戏目录
        if os.path.exists(self.external_games_dir):
            for item in os.listdir(self.external_games_dir):
                game_path = os.path.join(self.external_games_dir, item)
                if os.path.isdir(game_path):
                    config_path = os.path.join(game_path, "config.json")
                    if os.path.exists(config_path):
                        games.append({
                            'name': item,
                            'path': game_path,
                            'config': config_path,
                            'assets': os.path.join(game_path, "assets")
                        })
        
        return games
    
    def get_game_info(self, game_name):
        """获取游戏信息"""
        game_path = os.path.join(self.external_games_dir, game_name)
        if not os.path.exists(game_path):
            return None
        
        return {
            'name': game_name,
            'path': game_path,
            'config': os.path.join(game_path, "config.json"),
            'assets': os.path.join(game_path, "assets")
        }
    
    def create_game(self, game_name):
        """创建新游戏配置"""
        game_path = os.path.join(self.external_games_dir, game_name)
        
        if os.path.exists(game_path):
            raise ValueError(f"游戏 {game_name} 已存在")
        
        # 创建目录结构
        os.makedirs(game_path, exist_ok=True)
        os.makedirs(os.path.join(game_path, "assets"), exist_ok=True)
        
        # 创建默认配置
        config_path = os.path.join(game_path, "config.json")
        default_config_path = os.path.join(self.base_dir, "config_default.json")
        
        if os.path.exists(default_config_path):
            shutil.copy(default_config_path, config_path)
            # 更新游戏名称
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            config['game_name'] = game_name
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        else:
            # 创建基础配置
            default_config = {
                "game_name": game_name,
                "strategies": []
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        return self.get_game_info(game_name)
    
    def load_game_to_current(self, game_name):
        """
        将指定游戏加载到 current_game 目录
        用于打包前的准备
        
        ⚠️  警告：此操作会覆盖 current_game 目录！
        """
        game_info = self.get_game_info(game_name)
        if not game_info:
            raise ValueError(f"游戏 {game_name} 不存在")
        
        # 检查 current_game 是否有内容，如果有则先备份
        if os.path.exists(self.current_game_dir):
            current_config = os.path.join(self.current_game_dir, "config.json")
            current_assets = os.path.join(self.current_game_dir, "assets")
            
            has_content = False
            if os.path.exists(current_config):
                has_content = True
            if os.path.exists(current_assets) and os.listdir(current_assets):
                has_content = True
            
            if has_content:
                import time
                backup_dir = f"current_game_backup_{int(time.time())}"
                print(f"⚠️  检测到 current_game 有内容，备份到: {backup_dir}")
                shutil.copytree(self.current_game_dir, backup_dir)
            
            # 清空 current_game 目录
            shutil.rmtree(self.current_game_dir)
        
        os.makedirs(self.current_game_dir, exist_ok=True)
        
        # 复制配置文件
        if os.path.exists(game_info['config']):
            shutil.copy(game_info['config'], 
                       os.path.join(self.current_game_dir, "config.json"))
        else:
            print(f"⚠️  警告: 游戏配置文件不存在")
        
        # 复制资源目录
        if os.path.exists(game_info['assets']):
            if os.listdir(game_info['assets']):  # 只有非空才复制
                shutil.copytree(game_info['assets'], 
                              os.path.join(self.current_game_dir, "assets"))
            else:
                os.makedirs(os.path.join(self.current_game_dir, "assets"), exist_ok=True)
                print(f"⚠️  警告: 游戏资源目录为空")
        else:
            os.makedirs(os.path.join(self.current_game_dir, "assets"), exist_ok=True)
        
        print(f"✅ 已加载游戏 {game_name} 到 current_game/")
        print(f"   配置: current_game/config.json")
        print(f"   资源: current_game/assets/")
        
        return self.current_game_dir
    
    def export_current_game(self, game_name):
        """
        将 current_game 导出为新游戏
        用于保存当前配置
        """
        if not os.path.exists(os.path.join(self.current_game_dir, "config.json")):
            raise ValueError("current_game 目录中没有配置文件")
        
        game_path = os.path.join(self.external_games_dir, game_name)
        
        # 如果游戏已存在，先备份
        if os.path.exists(game_path):
            import time
            backup_path = f"{game_path}_backup_{int(time.time())}"
            shutil.move(game_path, backup_path)
            print(f"📦 已备份原游戏到: {backup_path}")
        
        # 创建新游戏目录
        os.makedirs(game_path, exist_ok=True)
        
        # 复制配置
        shutil.copy(os.path.join(self.current_game_dir, "config.json"),
                   os.path.join(game_path, "config.json"))
        
        # 复制资源
        current_assets = os.path.join(self.current_game_dir, "assets")
        if os.path.exists(current_assets):
            shutil.copytree(current_assets, 
                          os.path.join(game_path, "assets"),
                          dirs_exist_ok=True)
        
        print(f"✅ 已导出游戏 {game_name} 到 games/{game_name}/")
        
        return self.get_game_info(game_name)
    
    def get_current_game_paths(self):
        """
        获取当前游戏的路径（用于运行时）
        统一使用 current_game 目录
        """
        current_config = os.path.join(self.current_game_dir, "config.json")
        current_assets = os.path.join(self.current_game_dir, "assets")
        
        # 确保目录存在
        os.makedirs(self.current_game_dir, exist_ok=True)
        os.makedirs(current_assets, exist_ok=True)
        
        # 如果配置不存在，从默认配置创建
        if not os.path.exists(current_config):
            default_config = os.path.join(self.base_dir, "config_default.json")
            if os.path.exists(default_config):
                import shutil
                shutil.copy(default_config, current_config)
                print(f"✅ 已创建默认配置: {current_config}")
        
        return {
            'config': current_config,
            'assets': current_assets
        }


if __name__ == "__main__":
    import sys
    
    manager = GameManager()
    
    # 命令行参数处理
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            # 列出所有游戏
            games = manager.list_games()
            print(f"找到 {len(games)} 个游戏:")
            for game in games:
                print(f"  - {game['name']}")
        
        elif command == "export":
            # 导出当前游戏
            if len(sys.argv) < 3:
                print("❌ 用法: python game_manager.py export <游戏名>")
                sys.exit(1)
            
            game_name = sys.argv[2]
            try:
                manager.export_current_game(game_name)
            except Exception as e:
                print(f"❌ 导出失败: {e}")
                sys.exit(1)
        
        elif command == "load":
            # 加载游戏到 current_game
            if len(sys.argv) < 3:
                print("❌ 用法: python game_manager.py load <游戏名>")
                sys.exit(1)
            
            game_name = sys.argv[2]
            try:
                manager.load_game_to_current(game_name)
            except Exception as e:
                print(f"❌ 加载失败: {e}")
                sys.exit(1)
        
        elif command == "create":
            # 创建新游戏
            if len(sys.argv) < 3:
                print("❌ 用法: python game_manager.py create <游戏名>")
                sys.exit(1)
            
            game_name = sys.argv[2]
            try:
                game_info = manager.create_game(game_name)
                print(f"✅ 已创建游戏: {game_info['name']}")
                print(f"   路径: {game_info['path']}")
            except Exception as e:
                print(f"❌ 创建失败: {e}")
                sys.exit(1)
        
        else:
            print(f"❌ 未知命令: {command}")
            print("\n可用命令:")
            print("  list                    - 列出所有游戏")
            print("  export <游戏名>         - 导出 current_game 为新游戏")
            print("  load <游戏名>           - 加载游戏到 current_game")
            print("  create <游戏名>         - 创建新游戏")
            sys.exit(1)
    
    else:
        # 无参数时显示帮助
        print("=== 游戏管理器 ===\n")
        print("用法: python game_manager.py <命令> [参数]\n")
        print("命令:")
        print("  list                    - 列出所有游戏")
        print("  export <游戏名>         - 导出 current_game 为新游戏")
        print("  load <游戏名>           - 加载游戏到 current_game")
        print("  create <游戏名>         - 创建新游戏")
        print("\n示例:")
        print("  python game_manager.py list")
        print("  python game_manager.py export 我的游戏")
        print("  python game_manager.py load 斗破奇兵")
        
        print("\n当前状态:")
        games = manager.list_games()
        print(f"  游戏数量: {len(games)}")
        paths = manager.get_current_game_paths()
        print(f"  当前配置: {paths['config']}")
        print(f"  当前资源: {paths['assets']}")
