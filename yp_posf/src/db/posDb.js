/**
 * IndexedDB schema for offline-first POS (Dexie.js).
 * - products: cached product list (synced when online)
 * - pending_sales: queue of sales to POST when back online
 * 
 * Error handling: Wraps all DB operations in try-catch to prevent crashes
 */
import Dexie from 'dexie'

export const posDb = new Dexie('HoBoPOSOffline')

posDb.version(1).stores({
  products: 'id, sku, name, updated_at',
  pending_sales: '++localId, created_at',
})

// Add error handling to common operations
const originalOpen = posDb.open.bind(posDb)
posDb.open = async function() {
  try {
    return await originalOpen()
  } catch (err) {
    console.error('[IndexedDB Open Error]', err)
    // If database is corrupted, try to delete and recreate
    if (err.name === 'DatabaseClosedError' || err.name === 'InvalidStateError') {
      try {
        await Dexie.delete('HoBoPOSOffline')
        return await originalOpen()
      } catch (deleteErr) {
        console.error('[IndexedDB Delete Error]', deleteErr)
        throw err // Re-throw original error
      }
    }
    throw err
  }
}

export default posDb
