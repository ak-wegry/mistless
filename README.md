# <img src="Images/mistless.bmp"> mistless
プログラム・トレース・ツール

- テキストファイルのブラウザ(表示／ページング)
- タグジャンプ機能による効率的なプログラム参照
- ファイル拡張子に応じたキーワード/コメントの色分け表示

![](https://github.com/ak-wegry/mistless/blob/main/Images/mistless_demo.png)

## 使い方

$ mistless.py [option] *filename* ...<br>
```
[option]
    -m filename : タグファイルの作成
    -t filename : タグファイルの指定(指定なし:tags)
    -x n        : タブストップの指定(指定なし:4)
```

## 環境

以下の環境でのみ動作を確認

- Windows10 (コマンドプロンプト)

## 機能仕様
- 入力ファイルの文字コード(UTF8, euc等)を表示画面の文字コードに変換して表示
- 入力ファイルの拡張子に応じて、キーワード/コメント等を色分け表示<br>
  (.py .h .cpp .c .awk に対応)
- 入力ファイルの拡張子に応じて、タグ情報を自動生成<br>
  (ただし、起動時にタグファイルを読み込んだ場合は、自動生成しない)
- 同一キーワードのタグ情報が複数ある場合は、選択してタグジャンプ可能

## 初期設定
環境変数 MISTLESS_INIT に設定されたファイルを起動時に読み込み、
ユーザキー定義を登録する。

＜書式＞<br>
　map 入力キーパターン 変換パターン<br>
　※パターン内の制御コードは、16進数(\xFF)/8進数(\777)で表記

## (キー)コマンド
|種別        |キー       |説明                                                           |
|------------|-----------|---------------------------------------------------------------|
|基本        |^H         |コマンドのヘルプを表示                                         |
|            |q          |終了                                                           |
|スクロール  |f,SPACE    |<n>画面先にスクロール(<n>指定なし:1画面)                       |
|            |b          |<n>画面前にスクロール(<n>指定なし:1画面)                       |
|            |d          |<n>半画面先にスクロール(<n>指定なし:半画面)                    |
|            |u          |<n>半画面前にスクロール(<n>指定なし:半画面)                    |
|            |j          |<n>行先にスクロール(<n>指定なし:1行)                           |
|            |k          |<n>行前にスクロール(<n>指定なし:1行)                           |
|            |>          |右へ<n>カラム分スクロール(<n>指定なし:画面幅の半分)            |
|            |<          |左へ<n>カラム分スクロール(<n>指定なし:画面幅の半分)            |
|タグジャンプ|i          |カーソル位置の文字列でタグジャンプ                             |
|            |I          |カーソル位置の文字列でタグジャンプ(複数タグ:メニューから選択)  |
|            |o          |タグジャンプ前の位置へ戻る                                     |
|            |r          |指定したタグファイルを追加読込み                               |
|カーソル移動|J          |カーソルを<n>行下に移動(<n>指定なし:1行)                       |
|            |K          |カーソルを<n>行上に移動(<n>指定なし:1行)                       |
|            |M          |カーソルを画面内中央行に移動                                   |
|            |l          |カーソルを次の<n>番目のキーワードに移動(<n>指定なし:1番目)     |
|            |h          |カーソルを前の<n>番目のキーワードに移動(<n>指定なし:1番目)     |
|            |g          |ファイルの<n>行目を表示(<n>指定なし:先頭行)                    |
|            |G          |ファイルの<n>行目を表示(<n>指定なし:最終行)                    |
|            |{,},[,]    |カーソル位置の括弧に対応する括弧へ移動                         |
|            |m<a-z>     |現在の画面/カーソル位置を入力キー文字へ設定                    |
|            |@          |現在の画面/カーソル位置を設定                                  |
|            |'<a-z>     |入力キー文字に設定された画面/カーソル位置へ移動                |
|            |''         |移動直前の画面/カーソル位置へ戻る                              |
|検索        |/          |指定した文字列で順方向検索(完全一致)                           |
|            |?          |指定した文字列で逆方向検索(完全一致)                           |
|            |           |　^G     カーソル位置の文字列を取込み                          |
|            |           |　^F     カーソルを右に移動                                    |
|            |           |　^B     カーソルを左に移動                                    |
|            |           |　^D     カーソル位置の文字を削除                              |
|            |           |　^H     カーソル前の文字を削除                                |
|            |           |　^N, ^P 検索履歴の文字列リストを表示                          |
|            |           |　ESC    入力のキャンセル                                      |
|            |n          |直前に実行された検索を順方向へ<n>回実行(<n>指定なし:1回)       |
|            |p          |直前に実行された検索を逆方向へ<n>回実行(<n>指定なし:1回)       |
|ファイル切替|N          |複数ファイル読込み時、<n>番後のファイルを表示(<n>指定なし:直後)|
|            |P          |複数ファイル読込み時、<n>番前のファイルを表示(<n>指定なし:直前)|
|その他      |t          |タブストップ幅を<n>に変更                                      |
|            |^G         |ファイル名、カーソル位置を表示                                 |
|            |^L         |画面の再表示(画面サイズを再取得)                               |

```
^X      Ctrl+Xを表す
<n>     コマンド直前に数字キーで指定される値
<a-z>   'a'～'z'の1文字キー入力を表す
```
