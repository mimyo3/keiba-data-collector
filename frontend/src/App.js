import React, { useState, useEffect } from 'react';
import './App.css';

// テーブルコンポーネント
const TableComponent = ({ data, columns, tableName, loading, error }) => {
  if (loading) {
    return <div className="loading">データを取得中...</div>;
  }
  
  if (error) {
    return <div className="error">APIに接続できません: {error}</div>;
  }

  // データが空の場合
  if (!data || data.length === 0) {
    return <div className="no-data">データがありません</div>;
  }

  return (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column, index) => (
              <th key={index}>{column.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {columns.map((column, colIndex) => (
                <td key={colIndex}>{row[column.key]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// メインアプリケーションコンポーネント
function App() {
  const [activeTable, setActiveTable] = useState('horse_race_results');
  const [columns, setColumns] = useState([]);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // APIからデータを取得
  const fetchTableData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/db/horse_race_results');
      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const jsonData = await response.json();
      console.log('API Response data:', jsonData);
      
      // APIから返されたキーを列名として使用
      if (jsonData.length > 0) {
        const keys = Object.keys(jsonData[0]);
        const newColumns = keys.map(key => ({
          key: key,
          header: key
        }));
        setColumns(newColumns);
        setData(jsonData);
      } else {
        setColumns([]);
        setData([]);
      }
    } catch (err) {
      console.error('APIエラー詳細:', err);
      setError('APIに接続できません: ' + err.message);
      setColumns([]);
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  // 初期ロード
  useEffect(() => {
    fetchTableData();
  }, []);

  // テーブル切り替え時の処理
  useEffect(() => {
    if (activeTable === 'horse_race_results') {
      fetchTableData();
    }
  }, [activeTable]);

  // テーブルリスト
  const tableList = [
    { name: 'horse_race_results', label: 'horse_race_results' },
    { name: 'table1', label: 'table1' },
    { name: 'table2', label: 'table2' },
  ];

  return (
    <div className="app">
      <header className="app-header">
        <h1>データベーステーブル表示</h1>
        <div className="table-buttons">
          {tableList.map((table) => (
            <button
              key={table.name}
              className={`table-button ${activeTable === table.name ? 'active' : ''}`}
              onClick={() => setActiveTable(table.name)}
            >
              {table.label}
            </button>
          ))}
        </div>
        <div className="links">
          <a href="/">ホーム</a>
          <a href="/race_date">開催日登録画面</a>
        </div>
      </header>
      
      <main className="app-main">
        <div className="table-wrapper">
          <TableComponent 
            data={data} 
            columns={columns} 
            tableName={activeTable}
            loading={loading}
            error={error}
          />
        </div>
      </main>
    </div>
  );
}

export default App;