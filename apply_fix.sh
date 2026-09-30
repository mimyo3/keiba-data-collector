#!/bin/bash

# 修正スクリプト: HomePage.js の無限スクロール機能追加

# ファイルのバックアップ
cp /home/nori/dev/autogen_test/sandbox/frontend/src/HomePage.js /home/nori/dev/autogen_test/sandbox/frontend/src/HomePage_backup.js

echo "修正を適用しています..."

# 1. TableViewコンポーネントの引数を変更
sed -i 's/const TableView = ({ activeTable, data, columns, loading, error, fetchTableData, currentPage, totalPages, totalRows, onPageChange })/const TableView = ({ activeTable, data, columns, loading, error, fetchTableData, currentPage, totalPages, totalRows, onPageChange, isScrollLoading, onLoadMore })/' /home/nori/dev/autogen_test/sandbox/frontend/src/HomePage.js

# 2. TableViewコンポーネント内のtable-containerのスタイルを変更
sed -i '/className="table-container"/s/className="table-container"/className="table-container" style={{ height: tableHeight, overflow: "auto" }} ref={tableRef}/' /home/nori/dev/autogen_test/sandbox/frontend/src/HomePage.js

# 3. TableViewコンポーネント内の無限スクロール用のロジックを追加
sed -i '/const handleScroll =/i\  const [tableHeight, setTableHeight] = useState("auto");\n  const tableRef = useRef(null);' /home/nori/dev/autogen_test/sandbox/frontend/src/HomePage.js

# 4. テーブルの高さを調整するロジックを追加
sed -i '/useEffect(() => {/a\    const handleResize = () => {\n      const windowHeight = window.innerHeight;\n      const headerHeight = 100; // ヘッダーの高さ\n      const controlsHeight = 100; // コントロールの高さ\n      const tableHeight = windowHeight - headerHeight - controlsHeight - 50;\n      setTableHeight(`${tableHeight}px`);\n    };\n\n    handleResize();\n    window.addEventListener("resize", handleResize);\n    return () => window.removeEventListener("resize", handleResize);\n  }, []);' /home/nori/dev/autogen_test/sandbox/frontend/src/HomePage.js

# 5. 無限スクロール機能を追加
sed -i '/const handleScroll = () => {/a\  // 無限スクロール用の監視\n  useEffect(() => {\n    const handleScroll = () => {\n      const scrollTop = window.scrollY || document.documentElement.scrollTop;\n      const windowHeight = window.innerHeight;\n      const documentHeight = document.documentElement.scrollHeight;\n      \n      // 画面の下部に近づいた場合に追加データを読み込む\n      if (documentHeight - scrollTop - windowHeight < 100 && !isScrollLoading && currentPage < totalPages) {\n        onLoadMore();\n      }\n    };\n\n    window.addEventListener("scroll", handleScroll);\n    return () => window.removeEventListener("scroll", handleScroll);\n  }, [isScrollLoading, currentPage, totalPages, onLoadMore]);' /home/nori/dev/autogen_test/sandbox/frontend/src/HomePage.js

# 6. ページング制限を解除するためにfetchTableDataの呼び出しを変更
sed -i '/fetchTableData(activeTable, newPage, 100);/c\      fetchTableData(activeTable, newPage, 10000);' /home/nori/dev/autogen_test/sandbox/frontend/src/HomePage.js

# 7. ページング制限を解除するためにfetchTableDataの引数を変更
sed -i '/const fetchTableData = async (tableName = activeTable, page = 1, limit = 100) =>/c\  const fetchTableData = async (tableName = activeTable, page = 1, limit = 10000) =>' /home/nori/dev/autogen_test/sandbox/frontend/src/HomePage.js

# 8. ページング制限を解除するためにAPIリクエストのlimitを変更
sed -i '/page=${page}&limit=${limit}/c\page=${page}&limit=${limit}' /home/nori/dev/autogen_test/sandbox/frontend/src/HomePage.js

# 9. ページング制限を解除するために、ページングの制限を削除
sed -i '/const limit = 100;/c\  const limit = 10000;' /home/nori/dev/autogen_test/sandbox/frontend/src/HomePage.js

echo "修正が完了しました。"
echo "ファイルの変更内容を確認してください。"