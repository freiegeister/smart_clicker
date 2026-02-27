#!/usr/bin/env python3
"""
游戏管理命令行工具
用于管理多个游戏的配置和资源
"""
import sys
import argparse
from game_manager import GameManager

def list_games(manager):
    """列出所有游戏"""
    games = manager.list_games()
    if not games:
        print("❌ 没有找到任何游戏配置")
        print(f"   游戏目录: {manager.external_games_dir}")
        return
    
    print(f"📁 找到 {len(games)} 个游戏:\n")
    for i, game in enumerate(games, 1):
        print(f"{i}. {game['name']}")
        print(f"   路径: {game['path']}")
        print(f"   配置: {game['config']}")
        print(f"   资源: {game['assets']}")
        print()

def create_game(manager, game_name):
    """创建新游戏"""
    try:
        game_info = manager.create_game(game_name)
        print(f"✅ 成功创建游戏: {game_name}")
        print(f"   路径: {game_info['path']}")
        print(f"   配置: {game_info['config']}")
        print(f"   资源: {game_info['assets']}")
    except ValueError as e:
        print(f"❌ 创建失败: {e}")
        sys.exit(1)

def load_game(manager, game_name):
    """加载游戏到 current_game（用于打包）"""
    try:
        current_dir = manager.load_game_to_current(game_name)
        print(f"\n💡 提示:")
        print(f"   1. 现在可以运行 gui.py 测试游戏")
        print(f"   2. 打包时只会包含 current_game/ 目录")
        print(f"   3. 修改后可以用 'export' 命令保存回去")
    except ValueError as e:
        print(f"❌ 加载失败: {e}")
        sys.exit(1)

def export_game(manager, game_name):
    """导出 current_game 为游戏配置"""
    try:
        game_info = manager.export_current_game(game_name)
        print(f"\n💡 提示:")
        print(f"   游戏配置已保存到 games/{game_name}/")
        print(f"   可以用 'load' 命令重新加载")
    except ValueError as e:
        print(f"❌ 导出失败: {e}")
        sys.exit(1)

def show_current(manager):
    """显示当前游戏路径"""
    paths = manager.get_current_game_paths()
    print("📍 当前游戏路径:")
    print(f"   配置: {paths['config']}")
    print(f"   资源: {paths['assets']}")
    
    import os
    if os.path.exists(paths['config']):
        import json
        with open(paths['config'], 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"\n游戏名称: {config.get('game_name', '未知')}")
        print(f"策略数量: {len(config.get('strategies', []))}")
    else:
        print("\n⚠️  配置文件不存在")

def main():
    parser = argparse.ArgumentParser(
        description='游戏配置管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 列出所有游戏
  python manage_games.py list
  
  # 创建新游戏
  python manage_games.py create my_game
  
  # 加载游戏到 current_game（准备打包）
  python manage_games.py load my_game
  
  # 导出 current_game 为游戏配置
  python manage_games.py export my_game
  
  # 显示当前游戏信息
  python manage_games.py current
  
  # 使用外部游戏目录
  python manage_games.py --games-dir /path/to/games list
        """
    )
    
    parser.add_argument(
        '--games-dir',
        help='外部游戏目录路径（默认: ./games）'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # list 命令
    subparsers.add_parser('list', help='列出所有游戏')
    
    # create 命令
    create_parser = subparsers.add_parser('create', help='创建新游戏')
    create_parser.add_argument('game_name', help='游戏名称')
    
    # load 命令
    load_parser = subparsers.add_parser('load', help='加载游戏到 current_game')
    load_parser.add_argument('game_name', help='游戏名称')
    
    # export 命令
    export_parser = subparsers.add_parser('export', help='导出 current_game 为游戏配置')
    export_parser.add_argument('game_name', help='游戏名称')
    
    # current 命令
    subparsers.add_parser('current', help='显示当前游戏信息')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 创建管理器
    manager = GameManager(external_games_dir=args.games_dir)
    
    # 执行命令
    if args.command == 'list':
        list_games(manager)
    elif args.command == 'create':
        create_game(manager, args.game_name)
    elif args.command == 'load':
        load_game(manager, args.game_name)
    elif args.command == 'export':
        export_game(manager, args.game_name)
    elif args.command == 'current':
        show_current(manager)

if __name__ == "__main__":
    main()
