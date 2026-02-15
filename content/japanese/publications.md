---
title: "業績"
draft: false
layout: "pages"
url: "publications/"
bg_image: "images/backgrounds/page-title.jpg"
description: "代表業績（抜粋）"
---

## 代表業績（抜粋）

### 年範囲で絞り込み

<div class="publication-filter-box">
  <label for="pub-year-from">開始年</label>
  <input id="pub-year-from" type="number" min="2000" max="2100" step="1" placeholder="例: 2021">
  <label for="pub-year-to">終了年</label>
  <input id="pub-year-to" type="number" min="2000" max="2100" step="1" placeholder="例: 2025">
  <button id="pub-apply" type="button" class="btn btn-sm btn-outline-primary">適用</button>
  <button id="pub-reset" type="button" class="btn btn-sm btn-outline-primary">リセット</button>
</div>

<p id="pub-filter-status" class="publication-filter-status">すべて表示中</p>

### 著書（抜粋）

<ol class="publication-list">
  <li class="publication-item" data-year="2021">
    <span class="publication-year">2021</span>
    <span class="publication-text">今こそ知りたい！ 学び続ける先生のための 基礎と実践から学べる小・中学校プログラミング教育</span>
  </li>
  <li class="publication-item" data-year="2019">
    <span class="publication-year">2019</span>
    <span class="publication-text">小・中・高等学校でのプログラミング教育実践 : 問題解決を目的とした論理的思考力の育成</span>
  </li>
</ol>

### 論文（抜粋）

<ol class="publication-list">
  <li class="publication-item" data-year="2025">
    <span class="publication-year">2025</span>
    <span class="publication-text">小学校における音楽リテラシーの向上を目指したICT活用による個別学習の効果</span>
  </li>
  <li class="publication-item" data-year="2025">
    <span class="publication-year">2025</span>
    <span class="publication-text">展示物とWebを連動させた情報遺産ギャラリーの構築</span>
  </li>
  <li class="publication-item" data-year="2024">
    <span class="publication-year">2024</span>
    <span class="publication-text">高校生の主体性及びGritと探究との関係</span>
  </li>
  <li class="publication-item" data-year="2022">
    <span class="publication-year">2022</span>
    <span class="publication-text">中学校の計測・制御システム学習におけるPythonを用いたプログラミング教育</span>
  </li>
  <li class="publication-item" data-year="2021">
    <span class="publication-year">2021</span>
    <span class="publication-text">小学校における簡単な動きのシミュレーションを取り入れたプログラミング授業実践の提案</span>
  </li>
</ol>

### 受賞

- 日本産業技術教育学会 論文賞（2018年度、2021年度）
- 日本産業技術教育学会 奨励賞（2021年度）
- 日本産業技術教育学会 学生優秀発表賞（2015年度）

<script>
  (function () {
    function parseYear(value) {
      if (!value) return null;
      var parsed = parseInt(value, 10);
      return Number.isNaN(parsed) ? null : parsed;
    }

    function applyPublicationFilter() {
      var from = parseYear(document.getElementById("pub-year-from").value);
      var to = parseYear(document.getElementById("pub-year-to").value);
      var items = document.querySelectorAll(".publication-item");
      var visibleCount = 0;

      items.forEach(function (item) {
        var year = parseInt(item.getAttribute("data-year"), 10);
        var show = true;
        if (from !== null && year < from) show = false;
        if (to !== null && year > to) show = false;
        item.style.display = show ? "" : "none";
        if (show) visibleCount += 1;
      });

      var status = document.getElementById("pub-filter-status");
      if (from === null && to === null) {
        status.textContent = "すべて表示中";
      } else {
        status.textContent = "表示件数: " + visibleCount + "件";
      }
    }

    function resetPublicationFilter() {
      document.getElementById("pub-year-from").value = "";
      document.getElementById("pub-year-to").value = "";
      applyPublicationFilter();
    }

    document.addEventListener("DOMContentLoaded", function () {
      var apply = document.getElementById("pub-apply");
      var reset = document.getElementById("pub-reset");
      apply.addEventListener("click", applyPublicationFilter);
      reset.addEventListener("click", resetPublicationFilter);
    });
  })();
</script>
