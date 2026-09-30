import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import HomePage from '../frontend/src/HomePage_updated.js';

// Mock fetch function
global.fetch = jest.fn();

describe('HomePage', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test('データ取得処理の正誤性検証', async () => {
    // モックデータ
    const mockData = [
      { id: 1, name: 'Test1', value: 100 },
      { id: 2, name: 'Test2', value: 200 }
    ];

    // モックレスポンス設定
    fetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockData),
      headers: new Map([['x-total-rows', '2']])
    });

    render(<HomePage />);

    // データが正しく表示されることを確認
    await waitFor(() => {
      expect(screen.getByText('Test1')).toBeInTheDocument();
      expect(screen.getByText('Test2')).toBeInTheDocument();
    });
  });

  test('ページング処理の確認', async () => {
    // モックデータ
    const mockData = [
      { id: 1, name: 'Test1', value: 100 },
      { id: 2, name: 'Test2', value: 200 }
    ];

    // モックレスポンス設定
    fetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockData),
      headers: new Map([['x-total-rows', '2']])
    });

    render(<HomePage />);

    // ページング情報が正しく表示されることを確認
    await waitFor(() => {
      expect(screen.getByText('1 / 1 ページ')).toBeInTheDocument();
    });
  });

  test('エラーハンドリングの確認', async () => {
    // エラーレスポンス設定
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      text: jest.fn().mockResolvedValue('Internal Server Error')
    });

    render(<HomePage />);

    // エラーが正しく表示されることを確認
    await waitFor(() => {
      expect(screen.getByText('APIに接続できません: HTTP error! status: 500. Internal Server Error')).toBeInTheDocument();
    });
  });
});
