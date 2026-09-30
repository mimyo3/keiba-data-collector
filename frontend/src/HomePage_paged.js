import React, { useState, useEffect, useRef } from 'react';
import './HomePage.css';

const PAGE_SIZE = 100;

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
        <label>
          開始日:
          <input 
            type="date" 
            value={startDate} 
            onChange={(e) => setStartDate(e.target.value)} 
          />
        </label>
        <label>
          終了日:
          <input 
            type="date" 
            value={endDate} 
            onChange={(e) => setEndDate(e.target.value)} 
          />
        </label>
      </div>
    </div>
  );
};

// テーブル表示コンポーネント
const TableView = ({ activeTable, data, columns, loading, error, isScrollLoading, fetchTableData, currentPage, totalPages, totalRows, onPageChange, onLoadMore }) => {
  const tableContainerRef = useRef(null);
  const tableList = [
    { name: 'horse_race_results', label: '馬場成績' },
    { name: 'html_saves', label: 'HTML保存' },
    { name: 'jra_html_metadata', label: 'JRA HTMLメタデータ' },
    { name: 'race_days', label: '開催日' },
    { name: 'race_fetch_status', label: 'レース取得状況' },
    { name: 'races', label: 'レース' },
  ];

  const handleScroll = (event) => {
    const container = event.currentTarget;
    if (container.scrollTop + container.clientHeight >= container.scrollHeight - 80) {
      onLoadMore();
    }
  };

  return (
    <div className="table-view">
      <h2>{activeTable} テーブル</h2>
      <div className="table-controls">
        {tableList.map((table) => (
          <button
            key={table.name}
            className={`table-button ${activeTable === table.name ? 'active' : ''}`}
            onClick={() => fetchTableData(table.name, 1, PAGE_SIZE)}
          >
            {table.label}
          </button>
        ))}
      </div>
      <div className="table-container" ref={tableContainerRef} onScroll={handleScroll} aria-label="テーブルデータ">
        {loading ? (
          <p>データを読み込み中...</p>
        ) : error && data.length === 0 ? (
          <p className="error">{error}</p>
        ) : data.length === 0 ? (
          <p className="no-data">データがありません</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column.key}>{column.header}</th>
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
              {isScrollLoading && (
                <tr><td colSpan={columns.length} className="loading-more">続きを読み込み中...</td></tr>
              )}
            </tbody>
          </table>
        )}
        {error && data.length > 0 && <p className="error">追加データを取得できませんでした: {error}</p>}
      </div>
      <div className="pagination-controls">
        <button onClick={() => onPageChange(currentPage - 1)} disabled={currentPage <= 1 || loading}>
          前へ
        </button>
        <span className="page-info">{currentPage} / {totalPages} ページ ({totalRows} 件)</span>
        <button onClick={() => onPageChange(currentPage + 1)} disabled={currentPage >= totalPages || loading}>
          次へ
        </button>
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
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRows, setTotalRows] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isScrollLoading, setIsScrollLoading] = useState(false);
  const loadMoreInProgress = useRef(false);
  
  console.log('HomePage component rendering, activeSection:', activeSection);

  // APIからデータを取得
  const fetchTableData = async (tableName = 'horse_race_results', page = 1, limit = PAGE_SIZE) => {
    try {
      setLoading(true);
      setError(null);
      setActiveTable(tableName);
      setCurrentPage(page);
      
      try {
        const response = await fetch(`/api/db/${tableName}?page=${page}&limit=${limit}`);
        console.log('Response status:', response.status);
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error('APIエラー詳細:', response.status, errorText);
          throw new Error(`HTTP error! status: ${response.status}. ${errorText}`);
        }
        
        const jsonData = await response.json();
        console.log('API Response data:', jsonData);
        
        const rowCount = Number(response.headers.get('x-total-rows') || 0);
        setTotalRows(rowCount);
        setTotalPages(Math.ceil(rowCount / limit));
        
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
    } catch (err) {
      console.error('fetchTableData error:', err);
      setError('データ取得に失敗しました: ' + err.message);
      setColumns([]);
      setData([]);
    }
  };

  const loadMoreData = async () => {
    if (loadMoreInProgress.current || loading || currentPage >= totalPages) return;
    loadMoreInProgress.current = true;
    setIsScrollLoading(true);
    const nextPage = currentPage + 1;
    try {
      const response = await fetch(`/api/db/${activeTable}?page=${nextPage}&limit=${PAGE_SIZE}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}. ${await response.text()}`);
      }
      const nextRows = await response.json();
      setData((currentRows) => [...currentRows, ...nextRows]);
      setCurrentPage(nextPage);
    } catch (err) {
      setError(err.message);
    } finally {
      loadMoreInProgress.current = false;
      setIsScrollLoading(false);
    }
  };

  // 初期ロード
  useEffect(() => {
    fetchTableData('horse_race_results', 1, PAGE_SIZE);
  }, []);
  
  // Handle page change
  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(parseInt(newPage));
      fetchTableData(activeTable, parseInt(newPage), PAGE_SIZE);
    }
  };

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
            isScrollLoading={isScrollLoading}
            fetchTableData={fetchTableData}
            currentPage={currentPage}
            totalPages={totalPages}
            totalRows={totalRows}
            onPageChange={handlePageChange}
            onLoadMore={loadMoreData}
          />
        )}
      </main>
    </div>
  );
};

export default HomePage;
