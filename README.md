# mistless
プログラム・トレース・ツール

- テキストファイルのブラウザ(表示／ページング)
- タグジャンプ機能による効率的なプログラム参照
- ファイル拡張子に応じたキーワード/コメントの色分け表示

## デモ
<tt>
<table>
<tr>
<td>
  <table>
    <tr width=300>
      <td bgcolor=#0000ff><font color=#ffffff>
      cmd.exe mistless.py test.py
      </td>
    </tr>
      <td bgcolor=#000000>
  <font color=#00aa00>def<font color=#ffffff> func1(id, args):<br>
  　<font color=#00aa00>if<font color=#ffffff> id == 1:<br>
  　　stat = <u>f</u>unc2(args)<br>
  　　:<br><br><br>
      </td>
    </tr>
      <td bgcolor=#ffffff><font color=#000000>
  test.py(1 of 1) 　　　　　　　[3, 12]
      </td>
    <tr>
    </tr>
  </table>
</td>

<td>
カーソル位置で┌→<br>
iキー押下　　 │<br>
───────┘<br><br>
←────────<br>
　　　　oキー押下
</td>

<td>
  <table>
    <tr width=300>
      <td bgcolor=#0000ff><font color=#ffffff>
      cmd.exe mistless.py test.py
      </td>
    </tr>
      <td bgcolor=#000000>
  <font color=#00aa00>def<font color=#ffffff> func2(args):<br>
  　stat = False<br>
  　<font color=#00aa00>for<font color=#ffffff> n <font color=#00aa00>in<font color=#ffffff> args:<br>
  　　s = func3(n)<br>
  　　:<br><br>
    </td>
    </tr>
      <td bgcolor=#ffffff><font color=#000000>
  test.py(1 of 1) 　　　　　　　 [7, 1]
      </td>
    <tr>
    </tr>
  </table>
</td>
</tr>
</table>

</tt>


## 使い方

$ mistless.py [option] *filename* ...
> <tt>
>   [option]<br>
>     -m *filename* : タグファイルの作成<br>
>     -t *filename* : タグファイルの指定(指定なし:tags)<br>
>     -x *n*        : タブストップの指定(指定なし:4)<br>
> </tt>

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
  ＜基本＞<br>
    ^H          コマンドのヘルプを表示<br>
    q           終了<br>
<br>
  ＜スクロール＞<br>
    f,SPACE     <n>画面先にスクロール(<n>指定なし:1画面)<br>
    b           <n>画面前にスクロール(<n>指定なし:1画面)<br>
    d           <n>半画面先にスクロール(<n>指定なし:半画面)<br>
    u           <n>半画面前にスクロール(<n>指定なし:半画面)<br>
    j           <n>行先にスクロール(<n>指定なし:1行)<br>
    k           <n>行前にスクロール(<n>指定なし:1行)<br>
    >           右へ<n>カラム分スクロール(<n>指定なし:画面幅の半分)<br>
    <           左へ<n>カラム分スクロール(<n>指定なし:画面幅の半分)<br>
<br>
  ＜タグジャンプ＞<br>
    i           カーソル位置の文字列でタグジャンプ<br>
    I           カーソル位置の文字列でタグジャンプ(複数タグ:メニューから選択)<br>
    o           タグジャンプ前の位置へ戻る<br>
    r           指定したタグファイルを追加読込み<br>
<br>
  ＜カーソル移動＞<br>
    J           カーソルを<n>行下に移動(<n>指定なし:1行)<br>
    K           カーソルを<n>行上に移動(<n>指定なし:1行)<br>
    M           カーソルを画面内中央行に移動<br>
    l           カーソルを次の<n>番目のキーワードに移動(<n>指定なし:1番目)<br>
    h           カーソルを前の<n>番目のキーワードに移動(<n>指定なし:1番目)<br>
    g           ファイルの<n>行目を表示(<n>指定なし:先頭行)<br>
    G           ファイルの<n>行目を表示(<n>指定なし:最終行)<br>
    {,},[,]     カーソル位置の括弧に対応する括弧へ移動<br>
    m<a-z>      現在の画面/カーソル位置を入力キー文字へ設定<br>
    @           現在の画面/カーソル位置を設定<br>
    '<a-z>      入力キー文字に設定された画面/カーソル位置へ移動<br>
    ''          移動直前の画面/カーソル位置へ戻る<br>
<br>
  ＜検索＞<br>
    /           指定した文字列で順方向検索(完全一致)<br>
    ?           指定した文字列で逆方向検索(完全一致)<br>
                  ^G     カーソル位置の文字列を取込み<br>
                  ^F     カーソルを右に移動<br>
                  ^B     カーソルを左に移動<br>
                  ^D     カーソル位置の文字を削除<br>
                  ^H     カーソル前の文字を削除<br>
                  ^N, ^P 検索履歴の文字列リストを表示<br>
                  ESC    入力のキャンセル<br>
    n           直前に実行された検索を順方向へ<n>回実行(<n>指定なし:1回)<br>
    p           直前に実行された検索を逆方向へ<n>回実行(<n>指定なし:1回)<br>
<br>
  ＜ファイル切替＞<br>
    N           複数ファイル読込み時、<n>番後のファイルを表示(<n>指定なし:直後)<br>
    P           複数ファイル読込み時、<n>番前のファイルを表示(<n>指定なし:直前)<br>
<br>
  ＜その他＞<br>
    t           タブストップ幅を<n>に変更<br>
    ^G          ファイル名、カーソル位置を表示<br>
    ^L          画面の再表示(画面サイズを再取得)<br>
<br>
  ＜※＞<br>
    ^X          Ctrl+Xを表す<br>
    <n>         コマンド直前に数字キーで指定される値<br>
    <a-z>       'a'～'z'の1文字キー入力を表す<br>
