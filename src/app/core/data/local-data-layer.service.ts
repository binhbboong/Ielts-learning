import { Inject, Injectable, InjectionToken } from '@angular/core';
import { IndexedDbClient, ObjectStoreConfig } from './indexed-db-client';

const DB_NAME = 'ielts-learning-dashboard';
const DB_VERSION = 1;

/**
 * Injection token for the database name, so Angular's DI (and its AOT compiler) has a
 * resolvable token for this constructor parameter. Tests bypass DI entirely and construct
 * `new LocalDataLayerService(customName)` directly, so this token only matters for the
 * real `providedIn: 'root'` singleton path.
 */
export const LOCAL_DATA_LAYER_DB_NAME = new InjectionToken<string>('LOCAL_DATA_LAYER_DB_NAME', {
  providedIn: 'root',
  factory: () => DB_NAME,
});

/**
 * The single shared persistence schema named in docs/architecture/Architecture.md's
 * "Local Data Layer" component. Every feature module's repository reads/writes through
 * this service rather than touching IndexedDB directly. New feature modules add their own
 * store configs here rather than opening a second database.
 */
const STORES: ObjectStoreConfig[] = [
  { name: 'tasks', keyPath: 'id', indexes: [{ name: 'byDayNumber', keyPath: 'dayNumber' }] },
  // planState is a single record with no natural key of its own, so it's stored with an
  // explicit out-of-line key ('current') rather than a keyPath on the PlanState model.
  { name: 'planState' },
];

@Injectable({ providedIn: 'root' })
export class LocalDataLayerService {
  private readonly client: IndexedDbClient;

  constructor(@Inject(LOCAL_DATA_LAYER_DB_NAME) dbName: string) {
    this.client = new IndexedDbClient(dbName, DB_VERSION, STORES);
  }

  put<T>(storeName: string, value: T, key?: IDBValidKey): Promise<void> {
    return this.client.put(storeName, value, key);
  }

  get<T>(storeName: string, key: IDBValidKey): Promise<T | undefined> {
    return this.client.get(storeName, key);
  }

  getAll<T>(storeName: string): Promise<T[]> {
    return this.client.getAll(storeName);
  }

  getAllByIndex<T>(storeName: string, indexName: string, value: IDBValidKey): Promise<T[]> {
    return this.client.getAllByIndex(storeName, indexName, value);
  }
}
