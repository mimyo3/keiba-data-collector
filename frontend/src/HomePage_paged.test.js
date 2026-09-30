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
});