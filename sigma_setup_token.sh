#!/bin/bash
# Sigma setup token - يحفظ التوكين من غير ما يظهر، ومن غير ما يتحفظ في الهيستوري
# Run: bash sigma_setup_token.sh
echo "هتلصق التوكين دلوقتي - مش هيبان وانت بتلصقه، ده طبيعي."
echo "متحطش التوكين في الشات. هنا بس في Termux."
read -s -p "Paste GitHub token (ghp_...): " TOK
echo ""
if [ -z "$TOK" ]; then echo "مكتبتش حاجة - ملغاة."; exit 1; fi
printf "%s" "$TOK" > ~/token.txt
chmod 600 ~/token.txt
echo "اتحفظ في ~/token.txt - طوله: $(wc -c < ~/token.txt) حرف"
echo "دلوقتي شغل: bash sigma_termux_rescue.sh"
