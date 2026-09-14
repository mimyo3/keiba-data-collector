import React, { useState } from 'react';
import './HomePage.css';

// データ登録コンポーネント
const DataRegistrationSection = () => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [isFetching, setIsFetching] = useState(false);
  const [isNetkeibaFetching, setIsNetkeibaFetching] = useState(false);

  const handleJraFetch = async () => {
    console.log('JRA fetch button clicked');
    // 日付が指定されていない場合、現在月から1ヶ月前までの範囲を設定
    let startMonth = startDate || new Date().toISOString().slice(0, 7).replace(/-/g, '');
    let endMonth = endDate || new Date(new Date().setDate(1)).toISOString().slice(0, 7).replace(/-/g, '');
    
    // 現在の日付から1ヶ月前を取得
    const today = new Date();
    const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
    const defaultStartMonth = lastMonth.toISOString().slice(0, 7).replace(/-/g, '');
    
    // デフォルト値を設定
    if (!startDate) {
      startMonth = defaultStartMonth;
    }
    if (!endDate) {
      endMonth = defaultStartMonth;
    }
    
    // 日付形式をYYYYMM形式に変換
    const formatMonth = (dateString) => {
      if (!dateString) return '';
      const date = new Date(dateString);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      return `${year}${month}`;
    };
    
    const formattedStartMonth = formatMonth(startDate || new Date());
    const formattedEndMonth = formatMonth(endDate || new Date());
    
    console.log('JRA fetch parameters - startMonth:', startMonth, 'endMonth:', endMonth);
    
    setIsFetching(true);
    
    try {
      const response = await fetch('/api/jra/fetch-race-days', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start_month: formattedStartMonth,
          end_month: formattedEndMonth
        }),
      });
      
      console.log('JRA fetch response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}. ${errorText}`);
      }
      
      const result = await response.json();
      alert(`JRA開催日取得が成功しました！\n${result.message}`);
    } catch (error) {
      console.error('JRA開催日取得エラー:', error);
      alert(`JRA開催日取得に失敗しました: ${error.message}`);
    } finally {
      setIsFetching(false);
    }
  };

  const handleNetkeibaFetch = async () => {
    console.log('netkeiba fetch button clicked');
    // 日付が指定されていない場合、現在日付を設定
    const defaultStartDate = startDate || new Date().toISOString().slice(0, 10);
    const defaultEndDate = endDate || new Date().toISOString().slice(0, 10);
    
    console.log('Start date:', defaultStartDate);
    console.log('End date:', defaultEndDate);
    
    setIsNetkeibaFetching(true);
    
    try {
      console.log('Sending fetch request to /api/netkeiba/fetch-data-by-date-range');
      const response = await fetch('/api/netkeiba/fetch-data-by-date-range', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start_date: defaultStartDate,
          end_date: defaultEndDate
        }),
      });
      
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('HTTP error response text:', errorText);
        throw new Error(`HTTP error! status: ${response.status}. ${errorText}`);
      }
      
      const result = await response.json();
      console.log('Fetch result:', result);
      alert(`netkeiba情報取得が成功しました！\n${result.message}`);
    } catch (error) {
      console.error('netkeiba情報取得エラー:', error);
      alert(`netkeiba情報取得に失敗しました: ${error.message}`);
    } finally {
      setIsNetkeibaFetching(false);
    }
  };

  console.log('DataRegistrationSection rendering with isFetching:', isFetching, 'isNetkeibaFetching:', isNetkeibaFetching);
  
  return (
    <div className="data-registration-section">
      <h2>データ登録</h2>
      <div className="registration-buttons">
        <button 
          className="register-button" 
          onClick={handleJraFetch}
          disabled={isFetching}
        >
          {isFetching ? 'ＪＲＡ取得中...' : 'ＪＲＡ開催日取得'}
        </button>
        <button 
          className="register-button" 
          onClick={handleNetkeibaFetch}
          disabled={isNetkeibaFetching}
        >
          {isNetkeibaFetching ? 'netkeiba取得中...' : 'netkeiba情報取得'}
        </button>
      </div>
      
      <div className="date-inputs">
        <h3>日付範囲指定</h3>
        <div className="date-input-group">
          <label htmlFor="start-date">開始日:</label>
          <input
            type="date"
            id="start-date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>
        <div className="date-input-group">
          <label htmlFor="end-date">終了日:</label>
          <input
            type="date"
            id="end-date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>
      </div>
    </div>
  );
};

// テーブル表示コンポーネント
const TableView = ({ activeTable, data, columns, loading, error, fetchTableData }) => {
  // テーブルリスト
  const tableList = [
    { name: 'horse_race_results', label: 'horse_race_results' },
    { name: 'html_saves', label: 'html_saves' },
    { name: 'jra_html_metadata', label: 'jra_html_metadata' },
    { name: 'race_days', label: 'race_days' },
    { name: 'race_fetch_status', label: 'race_fetch_status' },
    { name: 'races', label: 'races' },
  ];

  return (
    <div className="table-view-section">
      <h2>テーブル表示</h2>
      <div className="table-controls">
        {tableList.map((table) => (
          <button 
            key={table.name}
            className={`table-button ${activeTable === table.name ? 'active' : ''}`}
            onClick={() => fetchTableData(table.name)}
          >
            {table.label}
          </button>
        ))}
      </div>
      
      <div className="table-container">
        {loading ? (
          <div className="loading">データを取得中...</div>
        ) : error ? (
          <div className="error">APIに接続できません: {error}</div>
        ) : !data || data.length === 0 ? (
          <div className="no-data">データがありません</div>
        ) : (
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
        )}
      </div>
    </div>
  );
};

// メインのホームページコンポーネント
const HomePage = () => {
  const [activeSection, setActiveSection] = useState('data-registration');
  const [activeTable, setActiveTable] = useState('horse_race_results');
  const [columns, setColumns] = useState([]);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  console.log('HomePage component rendering, activeSection:', activeSection);

  // APIからデータを取得
  const fetchTableData = async (tableName = 'horse_race_results') => {
    setLoading(true);
    setError(null);
    setActiveTable(tableName);
    
    try {
      const response = await fetch(`/api/db/${tableName}`);
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('APIエラー詳細:', response.status, errorText);
        throw new Error(`HTTP error! status: ${response.status}. ${errorText}`);
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
  React.useEffect(() => {
    fetchTableData();
  }, []);

  return (
    <div className="home-page">
      <header className="home-header">
        <h1>データベース管理システム</h1>
        <nav className="section-navigation">
          <button
            className={`nav-button ${activeSection === 'data-registration' ? 'active' : ''}`}
            onClick={() => setActiveSection('data-registration')}
          >
            データ登録
          </button>
          <button
            className={`nav-button ${activeSection === 'table-view' ? 'active' : ''}`}
            onClick={() => setActiveSection('table-view')}
          >
            テーブル表示
          </button>
        </nav>
        <div className="links">
          <a href="/">ホーム</a>
          <a href="/race_date">開催日登録画面</a>
        </div>
      </header>
      
      <main className="home-main">
        {activeSection === 'data-registration' ? (
          <DataRegistrationSection />
        ) : (
          <TableView 
            activeTable={activeTable}
            data={data}
            columns={columns}
            loading={loading}
            error={error}
            fetchTableData={fetchTableData}
          />
        )}
      </main>
    </div>
  );
};

export default HomePage;