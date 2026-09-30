import { PagingParams, PagingAdapter } from '../../frontend/src/paging/PagingAdapter';

describe('PagingParams', () => {
  test('ページングパラメータの正しく設定されることの確認', () => {
    const params = new PagingParams(2, 50);
    expect(params.page).toBe(2);
    expect(params.limit).toBe(50);
    expect(params.offset).toBe(50); // (2-1) * 50
  });

  test('ページ番号を変更できることの確認', () => {
    const params = new PagingParams(1, 100);
    params.setPage(3);
    expect(params.page).toBe(3);
    expect(params.offset).toBe(200); // (3-1) * 100
  });

  test('件数を変更できることの確認', () => {
    const params = new PagingParams(1, 100);
    params.setLimit(200);
    expect(params.limit).toBe(200);
    expect(params.offset).toBe(0); // (1-1) * 200
  });

  test('ページングパラメータをオブジェクトとして取得できることの確認', () => {
    const params = new PagingParams(2, 150);
    const result = params.toObject();
    expect(result).toEqual({
      page: 2,
      limit: 150,
      offset: 150 // (2-1) * 150
    });
  });
});

describe('PagingAdapter', () => {
  test('ページングアダプターの初期化確認', () => {
    const adapter = new PagingAdapter();
    expect(adapter.getCurrentPage()).toBe(1);
    expect(adapter.getLimit()).toBe(100);
  });

  test('ページ番号を設定できることの確認', () => {
    const adapter = new PagingAdapter();
    adapter.setPage(5);
    expect(adapter.getCurrentPage()).toBe(5);
  });

  test('件数を設定できることの確認', () => {
    const adapter = new PagingAdapter();
    adapter.setLimit(200);
    expect(adapter.getLimit()).toBe(200);
  });

  test('ページングパラメータを取得できることの確認', () => {
    const adapter = new PagingAdapter();
    adapter.setPage(3);
    adapter.setLimit(75);
    const params = adapter.getParams();
    expect(params).toEqual({
      page: 3,
      limit: 75,
      offset: 150 // (3-1) * 75
    });
  });

  test('ページ数の計算が正しく行われることの確認', () => {
    const adapter = new PagingAdapter();
    const totalPages = adapter.calculateTotalPages(250);
    expect(totalPages).toBe(3); // ceil(250/100) = 3
  });

  test('ページ数が100件ごとの計算されることの確認', () => {
    const adapter = new PagingAdapter();
    const totalPages = adapter.calculateTotalPages(1000);
    expect(totalPages).toBe(10); // ceil(1000/100) = 10
  });
});

describe('ApiPagingAdapter', () => {
  test('APIページングアダプターの初期化確認', () => {
    const mockApiCall = jest.fn();
    const adapter = new ApiPagingAdapter(mockApiCall, 50);
    expect(adapter.getPageSize()).toBe(50);
    expect(adapter.getCurrentPage()).toBe(1);
  });

  test('ページングデータを取得できることの確認', async () => {
    const mockApiCall = jest.fn().mockResolvedValue({ data: ['item1', 'item2'] });
    const adapter = new ApiPagingAdapter(mockApiCall);
    const result = await adapter.getPagedData(2);
    expect(mockApiCall).toHaveBeenCalledWith({ page: 2, size: 100 });
    expect(result).toEqual({ data: ['item1', 'item2'] });
  });

  test('追加パラメータを含めてページングデータを取得できることの確認', async () => {
    const mockApiCall = jest.fn().mockResolvedValue({ data: ['item1', 'item2'] });
    const adapter = new ApiPagingAdapter(mockApiCall);
    const result = await adapter.getPagedData(1, { filter: 'active' });
    expect(mockApiCall).toHaveBeenCalledWith({ page: 1, size: 100, filter: 'active' });
    expect(result).toEqual({ data: ['item1', 'item2'] });
  });

  test('総件数を取得できることの確認', async () => {
    const mockApiCall = jest.fn().mockResolvedValue({ totalCount: 250 });
    const adapter = new ApiPagingAdapter(mockApiCall);
    const count = await adapter.getTotalCount();
    expect(mockApiCall).toHaveBeenCalledWith({ page: 1, size: 1, count: true });
    expect(count).toBe(250);
  });

  test('ページサイズを設定できることの確認', () => {
    const mockApiCall = jest.fn();
    const adapter = new ApiPagingAdapter(mockApiCall, 50);
    adapter.setPageSize(75);
    expect(adapter.getPageSize()).toBe(75);
  });

  test('ページ番号を設定できることの確認', () => {
    const mockApiCall = jest.fn();
    const adapter = new ApiPagingAdapter(mockApiCall);
    adapter.setCurrentPage(3);
    expect(adapter.getCurrentPage()).toBe(3);
  });
});
