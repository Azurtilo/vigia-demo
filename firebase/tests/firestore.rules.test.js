// Pruebas de las reglas de Firestore contra el emulador.
// Ejecutar con: firebase emulators:exec --only firestore "npm --prefix firebase test"
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import {
  assertFails,
  assertSucceeds,
  initializeTestEnvironment,
} from '@firebase/rules-unit-testing'
import { doc, getDoc, setDoc, collection, getDocs } from 'firebase/firestore'
import { afterAll, beforeAll, beforeEach, describe, expect, it } from 'vitest'

const rulesPath = fileURLToPath(new URL('../firestore.rules', import.meta.url))

let env

beforeAll(async () => {
  env = await initializeTestEnvironment({
    projectId: 'demo-vigia-rules-test',
    firestore: { rules: readFileSync(rulesPath, 'utf8'), host: '127.0.0.1', port: 8080 },
  })
})

beforeEach(async () => {
  await env.clearFirestore()
  // Datos sembrados saltándose las reglas, como lo haría el backend con Admin SDK.
  await env.withSecurityRulesDisabled(async (ctx) => {
    const db = ctx.firestore()
    await setDoc(doc(db, 'users/ana'), { role: 'client', status: 'active' })
    await setDoc(doc(db, 'patients/p1'), { ownerUid: 'ana', status: 'active' })
  })
})

afterAll(async () => {
  await env?.cleanup()
})

describe('control: el emulador responde y los datos existen', () => {
  it('lee el paciente cuando las reglas están desactivadas (como Admin SDK)', async () => {
    await env.withSecurityRulesDisabled(async (ctx) => {
      const snap = await assertSucceeds(getDoc(doc(ctx.firestore(), 'patients/p1')))
      expect(snap.data()).toEqual({ ownerUid: 'ana', status: 'active' })
    })
  })
})

describe('acceso directo a Firestore desde clientes', () => {
  it('niega leer cualquier documento sin sesión', async () => {
    const db = env.unauthenticatedContext().firestore()
    await assertFails(getDoc(doc(db, 'patients/p1')))
  })

  it('niega al dueño leer su propio paciente directamente (debe usar la API)', async () => {
    const db = env.authenticatedContext('ana').firestore()
    await assertFails(getDoc(doc(db, 'patients/p1')))
  })

  it('niega que un usuario se asigne rol de administrador escribiendo su perfil', async () => {
    const db = env.authenticatedContext('ana').firestore()
    await assertFails(setDoc(doc(db, 'users/ana'), { role: 'admin', status: 'active' }))
  })

  it('niega listar colecciones completas', async () => {
    const db = env.authenticatedContext('ana').firestore()
    await assertFails(getDocs(collection(db, 'patients')))
  })

  it('niega crear documentos nuevos', async () => {
    const db = env.authenticatedContext('ana').firestore()
    await assertFails(setDoc(doc(db, 'patients/p2'), { ownerUid: 'ana' }))
  })

  it('niega el acceso aunque el token traiga un claim admin', async () => {
    const db = env.authenticatedContext('mallory', { role: 'admin' }).firestore()
    await assertFails(getDoc(doc(db, 'users/ana')))
  })
})
