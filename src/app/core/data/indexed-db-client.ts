export interface ObjectStoreIndexConfig {
  name: string;
  keyPath: string;
  unique?: boolean;
}

export interface ObjectStoreConfig {
  name: string;
  /** Omit for a store keyed by an explicit key passed at write time (e.g. a singleton record). */
  keyPath?: string;
  indexes?: ObjectStoreIndexConfig[];
}

/**
 * Generic, domain-agnostic wrapper around the browser IndexedDB API. Has no knowledge of
 * any feature's data shapes — every feature module's repository is built on top of this.
 */
export class IndexedDbClient {
  private readonly dbPromise: Promise<IDBDatabase>;

  constructor(
    private readonly dbName: string,
    private readonly version: number,
    private readonly stores: ObjectStoreConfig[],
  ) {
    this.dbPromise = this.open();
  }

  private open(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);

      request.onupgradeneeded = () => {
        const db = request.result;
        for (const store of this.stores) {
          if (db.objectStoreNames.contains(store.name)) {
            continue;
          }
          const objectStore = store.keyPath
            ? db.createObjectStore(store.name, { keyPath: store.keyPath })
            : db.createObjectStore(store.name);
          for (const index of store.indexes ?? []) {
            objectStore.createIndex(index.name, index.keyPath, { unique: index.unique ?? false });
          }
        }
      };

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async put<T>(storeName: string, value: T, key?: IDBValidKey): Promise<void> {
    const db = await this.dbPromise;
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readwrite');
      if (key === undefined) {
        tx.objectStore(storeName).put(value);
      } else {
        tx.objectStore(storeName).put(value, key);
      }
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  async get<T>(storeName: string, key: IDBValidKey): Promise<T | undefined> {
    const db = await this.dbPromise;
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const request = tx.objectStore(storeName).get(key);
      request.onsuccess = () => resolve(request.result as T | undefined);
      request.onerror = () => reject(request.error);
    });
  }

  async getAll<T>(storeName: string): Promise<T[]> {
    const db = await this.dbPromise;
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const request = tx.objectStore(storeName).getAll();
      request.onsuccess = () => resolve(request.result as T[]);
      request.onerror = () => reject(request.error);
    });
  }

  async getAllByIndex<T>(storeName: string, indexName: string, value: IDBValidKey): Promise<T[]> {
    const db = await this.dbPromise;
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const request = tx.objectStore(storeName).index(indexName).getAll(value);
      request.onsuccess = () => resolve(request.result as T[]);
      request.onerror = () => reject(request.error);
    });
  }
}
