# yomiyasu-chat

Claude Codeの会話応答を、結論ファーストで読みやすい自然な日本語にするoutput styleです。[nanaism/yomiyasu](https://github.com/nanaism/yomiyasu) の文体原則（主述の対応、擬人化と比喩動詞の排除、情報を足さない、太字と箇条書きの抑制など）を、推敲依頼時だけでなく毎回の応答に適用します。

yomiyasu本体は「渡された文章を書き直すスキル」であり、Claude Code自身の会話出力には発火しません。このリポジトリはその隙間を埋めるためのもので、yomiyasuスキルと併用できます。

## 使い方

### シンボリックリンクで使う（開発中の推奨）

```bash
git clone https://github.com/daichi-tomita-vivion/yomiyasu-chat.git ~/work/yomiyasu-chat
mkdir -p ~/.claude/output-styles
ln -s ~/work/yomiyasu-chat/output-styles/yomiyasu-chat.md ~/.claude/output-styles/yomiyasu-chat.md
```

`~/.claude/settings.json` に次を追加し、Claude Codeを再起動します。

```json
{ "outputStyle": "yomiyasu-chat" }
```

スタイルファイルは起動時に読み込まれるため、編集後は再起動が必要です。

### プラグインとして使う

```text
/plugin marketplace add daichi-tomita-vivion/yomiyasu-chat
/plugin install yomiyasu-chat@yomiyasu-chat
```

プラグインとして入れる場合は、同名のスタイルが二重に登録されるのを避けるため、上記のシンボリックリンクは削除してください。

## 改善の進め方

読みにくいと感じた応答があったら、どの文のどこが読みにくかったかを特定し、機械的に検証できるルールとして `output-styles/yomiyasu-chat.md` に1行足します。「簡潔に」のような曖昧な指示より、「文末のコロンを使わない」のような具体的な指示のほうが確実に守られます。1回の変更は1ルールに絞り、同じ質問で前後を比べます。

応答の機械的な測定には、yomiyasuに同梱の `yomiyasu_lint.py` が会話の応答にもそのまま使えます。

```bash
python3 ~/.claude/plugins/cache/yomiyasu/yomiyasu/1.0.6/scripts/yomiyasu_lint.py response.md
```

ルールが増えて回帰が気になり始めたら、`evals/` にケースを置いて `claude plugin eval .` でスタイルあり・なしのスコア差を測ります。

## ライセンス

MIT
