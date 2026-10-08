import React, { useState, useEffect, useRef, useCallback } from 'react';
import './HomePage.css';

const PAGE_SIZE = 100;

// データ登録コンポーネント
const DataRegistrationSection = ({ onFetchRaceCardUrls }) => {
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
        <button className="register-button" onClick={() => onFetchRaceCardUrls()}>
          当日出馬表URL取得
        </button>
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

const RaceCardUrlView = ({
  raceDate,
  onRaceDateChange,
  onSearchDate,
  raceCards,
  loading,
  error,
  fetchStatuses,
  onFetchPreviousRuns,
  onShowRaceCard,
  onBack,
}) => (
  <section className="race-card-url-view">
    <div className="race-card-url-heading">
      <h2>出馬表URL</h2>
      <button className="table-button" onClick={onBack}>データ登録へ戻る</button>
    </div>
    <form
      className="date-inputs"
      onSubmit={(event) => {
        event.preventDefault();
        onSearchDate(raceDate);
      }}
    >
      <label>
        開催日:
        <input
          type="date"
          value={raceDate}
          onChange={(event) => onRaceDateChange(event.target.value)}
          required
        />
      </label>
      <button className="table-button" type="submit" disabled={loading || !raceDate}>
        この日付の出馬表を表示
      </button>
    </form>
    {raceDate && <p>{raceDate} のレース: {raceCards.length} 件</p>}
    <div className="table-container" aria-label="出馬表URL一覧">
      {loading ? (
        <p>出馬表URLを取得中...</p>
      ) : error ? (
        <p className="error">出馬表URLを取得できませんでした: {error}</p>
      ) : raceCards.length === 0 ? (
        <p className="no-data">この日付の出馬表はありません</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>レースID</th>
              <th>出馬表URL</th>
              <th>出馬表表示</th>
              <th>前走記録取得</th>
            </tr>
          </thead>
          <tbody>
            {raceCards.map((race) => (
              <tr key={race.race_id}>
                <td>{race.race_id}</td>
                <td>
                  <a
                    href={race.url}
                    target="_blank"
                    rel="noreferrer"
                    onClick={() => onFetchPreviousRuns(race.race_id)}
                  >
                    {race.url}
                  </a>
                </td>
                <td>
                  <button
                    className="table-button"
                    onClick={() => onShowRaceCard(race)}
                  >
                    表示
                  </button>
                </td>
                <td aria-live="polite">
                  {fetchStatuses[race.race_id]?.message
                    || (race.fetch_status?.registered
                      ? '取得済み'
                      : race.fetch_status?.error_message
                        ? `取得失敗: ${race.fetch_status.error_message}`
                        : race.fetch_status
                          ? '未完了'
                          : '未取得')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  </section>
);

const RaceCardEntryView = ({
  raceDate,
  raceId,
  entries,
  loading,
  error,
  onBack,
}) => (
  <section className="race-card-url-view">
    <div className="race-card-url-heading">
      <h2>出馬表: {raceId}</h2>
      <button className="table-button" onClick={onBack}>
        出馬表URLへ戻る
      </button>
    </div>
    {!loading && !error && entries.length > 0 && (
      <p>{raceDate}・{entries.length}頭</p>
    )}
    <div className="table-container" aria-label="レース出馬表">
      {loading ? (
        <p role="status">登録済みの出馬表を読み込み中...</p>
      ) : error ? (
        <p className="error">出馬表を取得できませんでした: {error}</p>
      ) : entries.length === 0 ? (
        <p className="no-data">
          このレースの出馬表はまだ登録されていません。URLをクリックして取得してください。
        </p>
      ) : (
        <div className="race-card-newspaper">
          {entries.map((entry) => {
            const previousRuns = entry.previous_runs || [];
            const raceDayResult = entry.race_day_result || {
              race_id: entry.race_id,
              race_date: entry.race_date,
              horse_name: entry.horse_name,
              post: entry.horse_number,
              jockey: entry.jockey,
              weight: entry.carried_weight,
              horse_weight: entry.horse_weight,
              weight_change: entry.weight_change,
            };
            const subsequentRuns = entry.subsequent_runs || [];
            const timelineRuns = [
              ...subsequentRuns.slice().reverse().map((run, index) => ({
                ...run,
                display_label: `${subsequentRuns.length - index}走後`,
              })),
              { ...raceDayResult, display_label: '当日' },
              ...previousRuns.map((run, index) => ({
                ...run,
                display_label: index === 0 ? '前走' : `${index + 1}走前`,
              })),
            ];
            return (
              <article
                className="race-card-horse-row"
                key={`${entry.race_id}-${entry.horse_number}`}
              >
                <section className="race-card-horse-summary" aria-label="出走馬情報">
                  <div className="race-card-horse-number">
                    <span>{entry.frame_number ?? '-'}枠</span>
                    <strong>{entry.horse_number}</strong>
                  </div>
                  <div>
                    <h3>{entry.horse_name}</h3>
                    <p>{entry.sex_age || '-'}・{entry.carried_weight ?? '-'}kg</p>
                    <p>{entry.jockey || '-'} / {[entry.trainer_area, entry.trainer].filter(Boolean).join(' ') || '-'}</p>
                    <p>
                      馬体重 {entry.horse_weight ?? '-'}
                      {entry.weight_change == null ? '' : ` (${entry.weight_change > 0 ? '+' : ''}${entry.weight_change})`}
                      ・単勝 {entry.win_odds ?? '-'} ・{entry.popularity ?? '-'}人気
                    </p>
                  </div>
                </section>
                <section className="race-card-previous-runs" aria-label={`${entry.horse_name}の過去成績`}>
                  {timelineRuns.map((run, index) => (
                    <article
                      className={`race-card-previous-run ${
                        run.display_label === '当日'
                          ? 'race-card-run-day'
                          : run.display_label.endsWith('走後')
                            ? 'race-card-run-future'
                            : ''
                      }`}
                      key={`${run.race_id}-${run.display_label}-${index}`}
                    >
                      <h4>{run.display_label}</h4>
                      <p className="race-card-run-title">
                        {[
                          run.race_date || '開催日不明',
                          run.place_num,
                          run.race_id && /^\d{12}$/.test(run.race_id)
                            ? `${run.race_id.slice(-2)}R`
                            : null,
                          run.grade,
                        ].filter(Boolean).join(' ')}
                      </p>
                      <p className="race-card-run-race-name">
                        {run.race_name || '-'}
                        {run.race_condition ? `・${run.race_condition}` : ''}
                        {run.tousu == null ? '' : `・${run.tousu}頭`}
                        {run.post == null ? '' : `・${run.post}番`}
                        {run.popularity == null ? '' : `・${run.popularity}人気`}
                      </p>
                      <p className="race-card-run-track">
                        {[run.track, run.distance && `${run.distance}m`, run.condition, run.bias]
                          .filter(Boolean).join('・') || '-'}
                      </p>
                      <p className="race-card-run-result">
                        {run.tyakujun == null
                          ? (run.display_label === '当日' ? '結果未登録' : '-')
                          : `${run.tyakujun}着`}
                        {run.time ? `・${run.time}` : ''}
                        {run.margin ? `・着差 ${run.margin}` : ''}
                        {run.pace ? `・${run.pace}` : ''}
                        {(run.staus || run.develop_type) ? `・${run.staus || run.develop_type}` : ''}
                      </p>
                      <p>
                        {run.jockey || '-'}
                        {run.weight == null ? '' : `・${run.weight}kg`}
                        {run.horse_weight == null ? '' : `・馬体重${run.horse_weight}kg`}
                        {run.weight_change == null ? '' : ` (${run.weight_change > 0 ? '+' : ''}${run.weight_change})`}
                      </p>
                      <p>
                        {run.first_half == null ? '' : `前半3F ${run.first_half}`}
                        {run.corners ? `・通過 ${run.corners}` : ''}
                        {run.huri1 ? ` (${run.huri1})` : ''}
                        {run.corner4 ? `・4角 ${run.corner4}` : ''}
                        {run.corner_position ? `・走行位置 ${run.corner_position}` : ''}
                        {run.second_half == null ? '' : `・後半3F ${run.second_half}`}
                      </p>
                      {(run.ichinuke != null || run.jitenn != null) && (
                        <p>
                          {run.ichinuke == null ? '' : `勝ち上がり ${run.ichinuke}頭`}
                          {run.jitenn == null ? '' : `・3着以内 ${run.jitenn}頭`}
                        </p>
                      )}
                      {(run.time_index_total != null || run.time_index_start != null
                        || run.time_index_run != null || run.time_index_finish != null) && (
                        <p>
                          指数 {[
                            run.time_index_total,
                            run.time_index_start,
                            run.time_index_run,
                            run.time_index_finish,
                          ].map((value) => value == null ? '-' : value).join(' / ')}
                        </p>
                      )}
                      {(run.running_type || run.ana04) && (
                        <p>
                          {run.running_type ? `ラップタイプ ${run.running_type}` : ''}
                          {run.running_type && run.ana04 ? '・' : ''}
                          {run.ana04 ? `不利 ${run.ana04}` : ''}
                        </p>
                      )}
                    </article>
                  ))}
                </section>
              </article>
            );
          })}
        </div>
      )}
    </div>
  </section>
);

// テーブル表示コンポーネント
const TableView = ({ activeTable, data, columns, loading, error, isScrollLoading, currentPage, totalPages, totalRows, onPageChange, onLoadMore, searchQuery, sortConfig, onSearchChange, onSortChange, onTableChange }) => {
  const tableContainerRef = useRef(null);
  const searchTimerRef = useRef(null);
  const [searchInput, setSearchInput] = useState(searchQuery);
  const tableList = [
    { name: 'horse_race_results', label: '馬場成績' },
    { name: 'race_card_entries', label: '当日出馬表' },
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

  const handleTableChange = (tableName) => {
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    setSearchInput('');
    onTableChange(tableName);
  };

  const handleSearchInput = (value) => {
    setSearchInput(value);
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(() => onSearchChange(value), 300);
  };

  useEffect(() => () => clearTimeout(searchTimerRef.current), []);

  const handleSort = (key) => {
    const direction = sortConfig.key === key && sortConfig.direction === 'asc' ? 'desc' : 'asc';
    onSortChange(key, direction);
  };

  return (
    <div className="table-view">
      <h2>{activeTable} テーブル</h2>
      <div className="table-controls">
        {tableList.map((table) => (
          <button
            key={table.name}
            className={`table-button ${activeTable === table.name ? 'active' : ''}`}
            onClick={() => handleTableChange(table.name)}
          >
            {table.label}
          </button>
        ))}
      </div>
      <div className="table-search-controls">
        <label htmlFor="table-search">テーブル内を検索</label>
        <input
          id="table-search"
          type="search"
          value={searchInput}
          onChange={(event) => handleSearchInput(event.target.value)}
          placeholder="テーブル全体から検索"
        />
        <span className="table-result-count" aria-live="polite">
          {totalRows} 件検索結果 / {data.length} 件表示中
        </span>
      </div>
      <div className="table-container" ref={tableContainerRef} onScroll={handleScroll} aria-label="テーブルデータ">
        {loading ? (
          <p>データを読み込み中...</p>
        ) : error && data.length === 0 ? (
          <p className="error">{error}</p>
        ) : data.length === 0 ? (
          <p className={searchQuery ? 'no-matches' : 'no-data'}>{searchQuery ? '検索結果がありません' : 'データがありません'}</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column.key} aria-sort={sortConfig.key === column.key ? (sortConfig.direction === 'asc' ? 'ascending' : 'descending') : 'none'}>
                    <button className="table-sort-button" onClick={() => handleSort(column.key)} aria-label={`${column.header}でソート`}>
                      {column.header}{sortConfig.key === column.key ? (sortConfig.direction === 'asc' ? ' ▲' : ' ▼') : ' ↕'}
                    </button>
                  </th>
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
  const [raceDate, setRaceDate] = useState('');
  const [raceCards, setRaceCards] = useState([]);
  const [raceCardLoading, setRaceCardLoading] = useState(false);
  const [raceCardError, setRaceCardError] = useState('');
  const [raceFetchStatuses, setRaceFetchStatuses] = useState({});
  const [selectedRaceCard, setSelectedRaceCard] = useState(null);
  const [raceCardEntries, setRaceCardEntries] = useState([]);
  const [raceCardEntriesLoading, setRaceCardEntriesLoading] = useState(false);
  const [raceCardEntriesError, setRaceCardEntriesError] = useState('');
  const [activeTable, setActiveTable] = useState('horse_race_results');
  const [columns, setColumns] = useState([]);
  const [data, setData] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRows, setTotalRows] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isScrollLoading, setIsScrollLoading] = useState(false);
  const loadMoreInProgress = useRef(false);
  const raceFetchInProgress = useRef(new Set());

  const fetchPreviousRuns = async (raceId) => {
    if (raceFetchInProgress.current.has(raceId)) return;

    raceFetchInProgress.current.add(raceId);
    setRaceFetchStatuses((statuses) => ({
      ...statuses,
      [raceId]: { message: '前走記録を取得・登録中...' },
    }));

    try {
      const response = await fetch(`/api/netkeiba/fetch-race-data/${raceId}`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }
      const result = await response.json();
      setRaceFetchStatuses((statuses) => ({
        ...statuses,
        [raceId]: { message: result.message },
      }));
    } catch (err) {
      console.error(`race_id ${raceId} の前走記録取得に失敗しました:`, err);
      setRaceFetchStatuses((statuses) => ({
        ...statuses,
        [raceId]: { message: `取得失敗: ${err.message}` },
      }));
    } finally {
      raceFetchInProgress.current.delete(raceId);
    }
  };

  const fetchRaceCardUrls = async (targetDate = '') => {
    setActiveSection('race-card-urls');
    setRaceCardLoading(true);
    setRaceCardError('');
    try {
      const query = targetDate
        ? `?${new URLSearchParams({ race_date: targetDate }).toString()}`
        : '';
      const response = await fetch(`/api/netkeiba/race-card-urls${query}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }
      const result = await response.json();
      setRaceDate(result.race_date);
      setRaceCards(result.race_cards);
      setRaceFetchStatuses(
        Object.fromEntries(
          result.race_cards.map((race) => {
            const status = race.fetch_status;
            const message = status?.registered
              ? '取得済み'
              : status?.error_message
                ? `取得失敗: ${status.error_message}`
                : status
                  ? '未完了'
                  : '未取得';
            return [race.race_id, { message }];
          }),
        ),
      );
    } catch (err) {
      setRaceCardError(err.message);
      setRaceCards([]);
    } finally {
      setRaceCardLoading(false);
    }
  };

  const showRaceCard = async (race) => {
    setSelectedRaceCard(race);
    setActiveSection('race-card-view');
    setRaceCardEntries([]);
    setRaceCardEntriesLoading(true);
    setRaceCardEntriesError('');

    try {
      const response = await fetch(
        `/api/netkeiba/race-card/${race.race_id}`,
      );
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }
      const result = await response.json();
      setRaceCardEntries(result.entries);
    } catch (err) {
      setRaceCardEntriesError(err.message);
    } finally {
      setRaceCardEntriesLoading(false);
    }
  };
  
  console.log('HomePage component rendering, activeSection:', activeSection);

  // APIからデータを取得
  const fetchTableData = useCallback(async (tableName = 'horse_race_results', page = 1, limit = PAGE_SIZE, search = '', sortBy = null, sortOrder = 'asc') => {
    try {
      setLoading(true);
      setError(null);
      setActiveTable(tableName);
      setCurrentPage(page);
      
      try {
        const query = new URLSearchParams({ page: String(page), limit: String(limit) });
        if (search) query.set('search', search);
        if (sortBy) {
          query.set('sort_by', sortBy);
          query.set('sort_order', sortOrder);
        }
        const response = await fetch(`/api/db/${tableName}?${query.toString()}`);
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
        setTotalPages(Math.max(1, Math.ceil(rowCount / limit)));
        
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
  }, []);

  const loadMoreData = async () => {
    if (loadMoreInProgress.current || loading || currentPage >= totalPages) return;
    loadMoreInProgress.current = true;
    setIsScrollLoading(true);
    const nextPage = currentPage + 1;
    try {
      const query = new URLSearchParams({ page: String(nextPage), limit: String(PAGE_SIZE) });
      if (searchQuery) query.set('search', searchQuery);
      if (sortConfig.key) {
        query.set('sort_by', sortConfig.key);
        query.set('sort_order', sortConfig.direction);
      }
      const response = await fetch(`/api/db/${activeTable}?${query.toString()}`);
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
  }, [fetchTableData]);
  
  // Handle page change
  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(parseInt(newPage));
      fetchTableData(activeTable, parseInt(newPage), PAGE_SIZE, searchQuery, sortConfig.key, sortConfig.direction);
    }
  };

  const handleSearchChange = (newSearch, tableName = activeTable) => {
    setSearchQuery(newSearch);
    fetchTableData(tableName, 1, PAGE_SIZE, newSearch, sortConfig.key, sortConfig.direction);
  };

  const handleSortChange = (key, direction, tableName = activeTable) => {
    setSortConfig({ key, direction });
    fetchTableData(tableName, 1, PAGE_SIZE, searchQuery, key, direction);
  };

  const handleTableChange = (tableName) => {
    setSearchQuery('');
    setSortConfig({ key: null, direction: 'asc' });
    fetchTableData(tableName, 1, PAGE_SIZE, '', null, 'asc');
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
          <DataRegistrationSection onFetchRaceCardUrls={fetchRaceCardUrls} />
        ) : activeSection === 'race-card-urls' ? (
          <RaceCardUrlView
            raceDate={raceDate}
            onRaceDateChange={setRaceDate}
            onSearchDate={fetchRaceCardUrls}
            raceCards={raceCards}
            loading={raceCardLoading}
            error={raceCardError}
            fetchStatuses={raceFetchStatuses}
            onFetchPreviousRuns={fetchPreviousRuns}
            onShowRaceCard={showRaceCard}
            onBack={() => setActiveSection('data-registration')}
          />
        ) : activeSection === 'race-card-view' ? (
          <RaceCardEntryView
            raceDate={raceCardEntries[0]?.race_date || raceDate}
            raceId={selectedRaceCard?.race_id || ''}
            entries={raceCardEntries}
            loading={raceCardEntriesLoading}
            error={raceCardEntriesError}
            onBack={() => setActiveSection('race-card-urls')}
          />
        ) : (
          <TableView 
            activeTable={activeTable}
            data={data}
            columns={columns}
            loading={loading}
            error={error}
            isScrollLoading={isScrollLoading}
            currentPage={currentPage}
            totalPages={totalPages}
            totalRows={totalRows}
            onPageChange={handlePageChange}
            onLoadMore={loadMoreData}
            searchQuery={searchQuery}
            sortConfig={sortConfig}
            onSearchChange={handleSearchChange}
            onSortChange={handleSortChange}
            onTableChange={handleTableChange}
          />
        )}
      </main>
    </div>
  );
};

export default HomePage;
