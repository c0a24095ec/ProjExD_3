import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5  # 爆弾の数
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
        screen.blit(self.img, self.rct)


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird:"Bird"):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        """
        self.img = pg.image.load(f"fig/beam.png")  # ビームSurface
        self.rct = self.img.get_rect()  # ビームRect
        self.rct.centery = bird.rct.centery  # こうかとんの中心縦座標
        self.rct.left = bird.rct.right  # こうかとんの右座標
        self.vx, self.vy = +5, 0

    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        if check_bound(self.rct) == (True, True):
            self.rct.move_ip(self.vx, self.vy)
            screen.blit(self.img, self.rct)    


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        # 画面端ギリギリに生成されないように余白をとる
        margin = 50
        self.rct.center = (
            random.randint(margin, WIDTH - margin),
            random.randint(margin, HEIGHT - margin),
        )
        # 各爆弾の速度をランダムに左右上下に分散させる
        self.vx = random.choice([-5, +5])
        self.vy = random.choice([-5, +5])

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)
        

class Score:
    """
    スコア表示を管理するクラス
    """
    def __init__(self):
        # フォント設定（日本語フォント名は環境依存のためSysFontで指定）
        try:
            self.fonto = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        except Exception:
            # フォールバック
            self.fonto = pg.font.SysFont(None, 30)
        self.color = (0, 0, 255)
        self.score = 0
        # 初期の描画Surface
        self.img = self.fonto.render(f"スコア: {self.score}", 0, self.color)
        self.rct = self.img.get_rect()
        # 画面左下（横100, 下から50）
        self.rct.center = (100, HEIGHT - 50)

    def update(self, screen: pg.Surface) -> None:
        """現在のスコアを描画用Surfaceにしてscreenにblitする"""
        self.img = self.fonto.render(f"スコア: {self.score}", 0, self.color)
        # 再計算（幅が変わる可能性があるため）
        self.rct = self.img.get_rect()
        self.rct.center = (100, HEIGHT - 50)
        screen.blit(self.img, self.rct)

    def add(self, points: int = 1) -> None:
        """スコアを加算する"""
        self.score += points


class Explosion:
    """
    爆発エフェクトを管理するクラス。
    explosion.gif とその左右反転を交互に表示して爆発を演出する。
    """
    def __init__(self, center: tuple[int, int], life: int = 20):
        # 元画像と左右反転画像を読み込む
        img = pg.image.load("fig/explosion.gif")
        flipped = pg.transform.flip(img, True, False)
        self.imgs = [img, flipped]
        self.rct = img.get_rect()
        self.rct.center = center
        self.life = life

    def update(self, screen: pg.Surface) -> None:
        """life を1減らし、lifeが正ならimgsを切り替えて描画する"""
        if self.life <= 0:
            return
        # 交互に切り替え（lifeの偶奇で選択）
        idx = (self.life % 2)
        screen.blit(self.imgs[idx], self.rct)
        self.life -= 1


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    # bomb = Bomb((255, 0, 0), 10)
    boms = []  # 爆弾用の空のリスト
    # for _ in range(NUM_OF_BOMBS):  # NUM_OF_BOMBS個の爆弾を生成し，リストに追加
    #     boms.append(Bomb((255, 0, 0), 10))
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]  # リスト内包表記で書くとこうなる
    beams: list[Beam] = []  # 複数ビームを格納するリスト
    score = Score()  # スコア管理
    explosions: list[Explosion] = []
    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でBeamクラスのインスタンス生成してリストに追加
                beams.append(Beam(bird))

        screen.blit(bg_img, [0, 0])
        
        for bomb in bombs:  # リストに入っている全ての爆弾について
            if bird.rct.colliderect(bomb.rct):
                # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                bird.change_img(8, screen)  # メソッドをクラスの中に作ってお渡ししている
                fonto = pg.font.Font(None, 80)
                txt = fonto.render("Game Over", True, (255, 0, 0))
                screen.blit(txt, [WIDTH//2-150, HEIGHT//2])
                pg.display.update()
                time.sleep(1)
                return
        
        for b, bomb in enumerate(bombs):  # 名何番目の爆弾かも取り出せる
            # 各ビームに対して衝突判定を行う
            for i, bm in enumerate(beams):
                if bm is None:
                    continue
                if bm.rct.colliderect(bomb.rct):
                    # ビームと爆弾の衝突判定
                    beams[i] = None
                    bombs[b] = None
                    bird.change_img(6, screen)
                    score.add(1)
                    # 爆発エフェクトを生成して追加
                    explosions.append(Explosion(bomb.rct.center))
        bombs = [bomb for bomb in bombs if bomb is not None ]

        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        # ビームの更新（描画と画面外チェック）
        for bm in beams:
            if bm is None:
                continue
            bm.update(screen)
        # ビームリストと爆弾リストのクリーンアップ
        beams = [bm for bm in beams if bm is not None and check_bound(bm.rct) == (True, True)]
        bombs = [bomb for bomb in bombs if bomb is not None]
        # 爆発の更新とクリーンアップ
        for ex in explosions:
            ex.update(screen)
        explosions = [ex for ex in explosions if ex.life > 0]
        for bomb in bombs:
            bomb.update(screen)
        # スコア表示更新
        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()