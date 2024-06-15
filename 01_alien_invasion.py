import sys
import pygame
import importlib
from time import sleep
from pygame.sprite import Group

# 动态导入 settings 模块
settings_module = importlib.import_module('02_settings')
Settings = settings_module.Settings

# 动态导入 ship 模块
ship_module = importlib.import_module('03_ship')
Ship = ship_module.Ship

# 动态导入 bullet 模块
bullet_module = importlib.import_module('04_bullet')
Bullet = bullet_module.Bullet

# 动态导入 alien 模块
alien_module = importlib.import_module('05_alien')
Alien = alien_module.Alien

# 动态导入 game_stats 模块
stats_module = importlib.import_module('06_game_stats')
GameStats = stats_module.GameStats

class AlienInvasion:
    """管理游戏资源和行为的类"""

    def __init__(self):
        """初始化游戏并创建游戏资源"""
        pygame.init()
        self.settings = Settings()
        self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))
        pygame.display.set_caption("Alien Invasion")

        self.stats = GameStats(self)
        self.ship = Ship(self)
        self.bullets = Group()
        self.aliens = Group()

        self._create_fleet()

    def run_game(self):
        """开始游戏主循环"""
        while True:
            self._check_events()
            if self.stats.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()
            self._update_screen()

    def _check_events(self):
        """响应按键和鼠标事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)

    def _check_keydown_events(self, event):
        """响应按键"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()
        elif event.key == pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_p:
            self._start_game()

    def _check_keyup_events(self, event):
        """响应松开"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        if event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _start_game(self):
        """开始新游戏"""
        self.stats.reset_stats()
        self.stats.game_active = True
        self.aliens.empty()
        self.bullets.empty()
        self._create_fleet()
        self.ship.center_ship()
        pygame.mouse.set_visible(False)  # 隐藏光标

    def _fire_bullet(self):
        """如果还没有到达限制，就发射一颗子弹"""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)
            print(f"Bullet fired, total bullets: {len(self.bullets)}")

    def _create_fleet(self):
        """创建外星人群"""
        alien = Alien(self)
        alien_width = alien.rect.width
        available_space_x = self.settings.screen_width - 2 * alien_width
        number_aliens_x = available_space_x // (2 * alien_width)

        number_rows = self._get_number_rows()

        # 创建多行外星人
        for row_number in range(number_rows):
            for alien_number in range(number_aliens_x):
                self._create_alien(alien_number, row_number)

    def _create_alien(self, alien_number, row_number):
        """创建一个外星人并将其放在当前行"""
        alien = Alien(self)
        alien_width = alien.rect.width
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
        self.aliens.add(alien)

    def _get_number_rows(self):
        """计算屏幕上可以容纳多少行外星人"""
        alien = Alien(self)
        alien_height = alien.rect.height
        ship_height = self.ship.rect.height
        available_space_y = (self.settings.screen_height - (3 * alien_height) - ship_height)
        number_rows = available_space_y // (2 * alien_height)
        return number_rows

    def _update_bullets(self):
        """更新子弹的位置并删除消失的子弹"""
        self.bullets.update()
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """响应子弹和外星人的碰撞"""
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)

        if not self.aliens:
            self.bullets.empty()
            self._create_fleet()

    def _update_aliens(self):
        """检查是否有外星人位于屏幕边缘，并更新外星人群中所有外星人的位置"""
        self._check_fleet_edges()
        self.aliens.update()

        # 检测外星人和飞船之间的碰撞
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()

        # 检查是否有外星人到达屏幕底部
        self._check_aliens_bottom()

    def _check_fleet_edges(self):
        """有外星人到达边缘时采取相应的措施"""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """将整群外星人下移，并改变它们的方向"""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _check_aliens_bottom(self):
        """检查是否有外星人到达屏幕底端"""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                self._ship_hit()
                break

    def _ship_hit(self):
        """响应飞船被外星人撞到"""
        if self.stats.ships_left > 0:
            self.stats.ships_left -= 1
            self.aliens.empty()
            self.bullets.empty()
            self._create_fleet()
            self.ship.center_ship()
            sleep(1)
        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True)  # 显示光标

    def _update_screen(self):
        """更新屏幕上的图像，并切换到新屏幕"""
        self.screen.fill(self.settings.bg_color)
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.ship.blitme()
        self.aliens.draw(self.screen)
        if not self.stats.game_active:
            self._draw_start_screen()
        pygame.display.flip()

    def _draw_start_screen(self):
        """显示开始屏幕"""
        font = pygame.font.SysFont(None, 48)
        start_text = font.render("Press P to Start", True, (0, 255, 0))
        self.screen.blit(start_text, (self.settings.screen_width / 2 - start_text.get_width() / 2, self.settings.screen_height / 2))

if __name__ == '__main__':
    ai = AlienInvasion()
    ai.run_game()
