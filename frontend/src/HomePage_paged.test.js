import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import HomePage from './HomePage_paged';

const createRows = (first, count) =>
  Array.from({ length: count }, (_, index) => ({ id: `row-${first + index}` }));

const createResponse = (rows, totalRows) => ({
  ok: true,
  json: async () => rows,
  headers: { get: () => String(totalRows) },
});

describe('table scrolling', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  test('scrolling to the bottom appends the next 100 rows', async () => {
    fetch
      .mockResolvedValueOnce(createResponse(createRows(1, 100), 250))
      .mockResolvedValueOnce(createResponse(createRows(101, 100), 250));

    render(<HomePage />);
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByRole('button', { name: 'テーブル表示' }));

    const container = screen.getByLabelText('テーブルデータ');
    Object.defineProperties(container, {
      scrollTop: { configurable: true, value: 1000 },
      clientHeight: { configurable: true, value: 400 },
      scrollHeight: { configurable: true, value: 1400 },
    });
    fireEvent.scroll(container);

    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    expect(fetch).toHaveBeenLastCalledWith('/api/db/horse_race_results?page=2&limit=100');
    expect(await screen.findByText('row-101')).toBeInTheDocument();
    expect(screen.getByText('row-100')).toBeInTheDocument();
  });

  test('search sends a full-table query and displays API results', async () => {
    fetch
      .mockResolvedValueOnce(createResponse([
        { id: 1, name: 'Sakura', score: 12 },
        { id: 2, name: 'Kitasan', score: 5 },
      ], 2))
      .mockResolvedValueOnce(createResponse([{ id: 2, name: 'Kitasan', score: 5 }], 1))
      .mockResolvedValueOnce(createResponse([], 0));

    render(<HomePage />);
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByRole('button', { name: 'テーブル表示' }));

    fireEvent.change(screen.getByRole('searchbox', { name: 'テーブル内を検索' }), { target: { value: '5' } });
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    expect(fetch).toHaveBeenLastCalledWith('/api/db/horse_race_results?page=1&limit=100&search=5');
    expect(screen.getByText('Kitasan')).toBeInTheDocument();
    expect(screen.queryByText('Sakura')).not.toBeInTheDocument();

    fireEvent.change(screen.getByRole('searchbox', { name: 'テーブル内を検索' }), { target: { value: 'no-match' } });
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));
    expect(screen.getByText('検索結果がありません')).toBeInTheDocument();
  });

  test('clicking a column header requests ascending and descending order', async () => {
    fetch
      .mockResolvedValueOnce(createResponse([
        { id: 'first', score: 20 },
        { id: 'second', score: 3 },
      ], 2))
      .mockResolvedValueOnce(createResponse([
        { id: 'second', score: 3 },
        { id: 'first', score: 20 },
      ], 2))
      .mockResolvedValueOnce(createResponse([
        { id: 'first', score: 20 },
        { id: 'second', score: 3 },
      ], 2));

    render(<HomePage />);
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByRole('button', { name: 'テーブル表示' }));

    const getVisibleRowValues = () => screen.getAllByRole('row').slice(1).map((row) => row.textContent);
    fireEvent.click(screen.getByRole('button', { name: 'scoreでソート' }));
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    expect(fetch).toHaveBeenLastCalledWith('/api/db/horse_race_results?page=1&limit=100&sort_by=score&sort_order=asc');
    await waitFor(() => expect(getVisibleRowValues()).toEqual(['second3', 'first20']));

    fireEvent.click(screen.getByRole('button', { name: 'scoreでソート' }));
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));
    expect(fetch).toHaveBeenLastCalledWith('/api/db/horse_race_results?page=1&limit=100&sort_by=score&sort_order=desc');
    await waitFor(() => expect(getVisibleRowValues()).toEqual(['first20', 'second3']));
  });

  test('fetching today\'s race-card URLs opens the URL table and clicking a link registers its previous runs', async () => {
    fetch
      .mockResolvedValueOnce(createResponse([{ id: 'row-1' }], 1))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          race_date: '2026-10-01',
          race_cards: [{ race_id: '202610010101', url: 'https://race.netkeiba.com/race/shutuba.html?race_id=202610010101' }],
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: '前走記録を取得してデータベースに登録しました。' }),
      });

    render(<HomePage />);
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByRole('button', { name: '当日出馬表URL取得' }));

    expect(await screen.findByRole('heading', { name: '当日出馬表URL' })).toBeInTheDocument();
    expect(await screen.findByText('202610010101')).toBeInTheDocument();
    const raceCardLink = screen.getByRole('link', { name: 'https://race.netkeiba.com/race/shutuba.html?race_id=202610010101' });
    expect(raceCardLink)
      .toHaveAttribute('href', 'https://race.netkeiba.com/race/shutuba.html?race_id=202610010101');
    expect(fetch).toHaveBeenLastCalledWith('/api/netkeiba/race-card-urls');

    fireEvent.click(raceCardLink);
    await waitFor(() => expect(fetch).toHaveBeenLastCalledWith(
      '/api/netkeiba/fetch-race-data/202610010101',
      { method: 'POST' },
    ));
    expect(await screen.findByText('前走記録を取得してデータベースに登録しました。')).toBeInTheDocument();
  });

  test('race-card display button opens a view containing only that race', async () => {
    fetch
      .mockResolvedValueOnce(createResponse([{ id: 'row-1' }], 1))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          race_date: '2026-10-03',
          race_cards: [
            { race_id: '202605040101', url: 'https://race.netkeiba.com/race/shutuba.html?race_id=202605040101' },
            { race_id: '202605040102', url: 'https://race.netkeiba.com/race/shutuba.html?race_id=202605040102' },
          ],
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          race_id: '202605040102',
          entries: [{
            race_id: '202605040102',
            race_date: '2026-10-03',
            frame_number: 2,
            horse_number: 3,
            horse_name: '対象レースの馬',
            sex_age: '牡3',
            carried_weight: 57,
            jockey: 'テスト騎手',
            trainer_area: '美浦',
            trainer: 'テスト厩舎',
            horse_weight: 480,
            weight_change: 2,
            win_odds: 4.5,
            popularity: 2,
            previous_runs: [
              {
                race_id: '202506010511',
                race_date: '2025-06-01',
                place_num: '東京',
                race_name: '日本ダービー',
                race_condition: '3歳',
                grade: 'G1',
                tousu: 18,
                post: 2,
                tyakujun: 1,
                popularity: 2,
                time: '2:25.0',
                margin: 'クビ',
                pace: 'M',
                staus: '持続戦',
                track: '芝',
                distance: 2400,
                condition: '良',
                bias: '内有利',
                jockey: '騎手B',
                weight: 57,
                horse_weight: 482,
                weight_change: 2,
                first_half: 35.1,
                corners: '1-1',
                huri1: '出遅れ',
                corner4: '4',
                corner_position: '内',
                second_half: 34.1,
                ichinuke: '3',
                jitenn: '5',
                time_index_total: 90,
                time_index_start: 80,
                time_index_run: 85,
                time_index_finish: 95,
                running_type: '瞬発型',
                ana04: '接触',
              },
              {
                race_id: '202505010511',
                race_date: '2025-05-01',
                place_num: '東京',
                race_name: '青葉賞',
                tyakujun: 4,
                time: '2:26.0',
                track: '芝',
                distance: 2400,
                condition: '良',
                jockey: '騎手A',
                weight: 56,
                horse_weight: 480,
                corners: '3-3',
                second_half: 35.2,
              },
            ],
          }],
        }),
      });

    render(<HomePage />);
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByRole('button', { name: '当日出馬表URL取得' }));
    await screen.findByRole('heading', { name: '当日出馬表URL' });

    const showButtons = screen.getAllByRole('button', { name: '表示' });
    expect(showButtons).toHaveLength(2);
    fireEvent.click(showButtons[1]);

    expect(await screen.findByRole('heading', { name: '当日出馬表: 202605040102' })).toBeInTheDocument();
    expect(fetch).toHaveBeenLastCalledWith('/api/netkeiba/race-card/202605040102');
    expect(await screen.findByText('対象レースの馬')).toBeInTheDocument();
    expect(screen.getByText('2026-10-03・1頭')).toBeInTheDocument();
    expect(screen.getByText('前走')).toBeInTheDocument();
    expect(screen.getByText('2走前')).toBeInTheDocument();
    const historyCards = document.querySelectorAll('.race-card-previous-run');
    expect(historyCards[0]).toHaveTextContent('2025-06-01 東京 11R G1');
    expect(historyCards[1]).toHaveTextContent('2025-05-01 東京 11R');
    expect(historyCards[0]).toHaveTextContent('日本ダービー');
    expect(historyCards[1]).toHaveTextContent('青葉賞');
    expect(historyCards[0]).toHaveTextContent('日本ダービー・3歳・18頭・2番・2人気');
    expect(historyCards[0]).toHaveTextContent('芝・2400m・良・内有利');
    expect(historyCards[0]).toHaveTextContent('1着・2:25.0・着差 クビ・M・持続戦');
    expect(historyCards[0]).toHaveTextContent('騎手B・57kg・馬体重482kg (+2)');
    expect(historyCards[0]).toHaveTextContent('前半3F 35.1・通過 1-1 (出遅れ)・4角 4・走行位置 内・後半3F 34.1');
    expect(historyCards[0]).toHaveTextContent('勝ち上がり 3頭・3着以内 5頭');
    expect(historyCards[0]).toHaveTextContent('指数 90 / 80 / 85 / 95');
    expect(historyCards[0]).toHaveTextContent('ラップタイプ 瞬発型・不利 接触');
    expect(screen.queryByText('202605040101')).not.toBeInTheDocument();
    expect(screen.queryByText(/お気に入り|馬メモ/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '当日出馬表URLへ戻る' }));
    expect(await screen.findByRole('heading', { name: '当日出馬表URL' })).toBeInTheDocument();
  });

  test('URL list shows previous-run fetches already registered in the database', async () => {
    fetch
      .mockResolvedValueOnce(createResponse([{ id: 'row-1' }], 1))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          race_date: '2026-10-03',
          race_cards: [{
            race_id: '202605040101',
            url: 'https://race.netkeiba.com/race/shutuba.html?race_id=202605040101',
            fetch_status: {
              html_fetched: true,
              parsed: true,
              registered: true,
              error_message: null,
            },
          }],
        }),
      });

    render(<HomePage />);
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByRole('button', { name: '当日出馬表URL取得' }));

    expect(await screen.findByText('取得済み')).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledTimes(2);
  });
});