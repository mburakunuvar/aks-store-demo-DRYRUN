'use strict'

const { test } = require('tap')
const { build } = require('../helper')

const validOrder = {
  storeId: 'store-001',
  customerOrderId: 'order-abc-123',
  items: [
    { productId: 1, quantity: 2 }
  ]
}

test('POST / accepts a valid order and returns 201', async (t) => {
  const app = await build(t)

  const res = await app.inject({
    method: 'POST',
    url: '/',
    payload: validOrder
  })
  t.equal(res.statusCode, 201)
})

test('POST / returns 400 when storeId is missing', async (t) => {
  const app = await build(t)

  const res = await app.inject({
    method: 'POST',
    url: '/',
    payload: { customerOrderId: 'order-abc-123', items: [{ productId: 1, quantity: 1 }] }
  })
  t.equal(res.statusCode, 400)
})

test('POST / returns 400 when customerOrderId is missing', async (t) => {
  const app = await build(t)

  const res = await app.inject({
    method: 'POST',
    url: '/',
    payload: { storeId: 'store-001', items: [{ productId: 1, quantity: 1 }] }
  })
  t.equal(res.statusCode, 400)
})

test('POST / returns 400 when items is missing', async (t) => {
  const app = await build(t)

  const res = await app.inject({
    method: 'POST',
    url: '/',
    payload: { storeId: 'store-001', customerOrderId: 'order-abc-123' }
  })
  t.equal(res.statusCode, 400)
})

test('POST / returns 400 when items array is empty', async (t) => {
  const app = await build(t)

  const res = await app.inject({
    method: 'POST',
    url: '/',
    payload: { storeId: 'store-001', customerOrderId: 'order-abc-123', items: [] }
  })
  t.equal(res.statusCode, 400)
})

test('POST / returns 400 when item is missing productId', async (t) => {
  const app = await build(t)

  const res = await app.inject({
    method: 'POST',
    url: '/',
    payload: { storeId: 'store-001', customerOrderId: 'order-abc-123', items: [{ quantity: 1 }] }
  })
  t.equal(res.statusCode, 400)
})

test('POST / returns 400 when item quantity is zero', async (t) => {
  const app = await build(t)

  const res = await app.inject({
    method: 'POST',
    url: '/',
    payload: { storeId: 'store-001', customerOrderId: 'order-abc-123', items: [{ productId: 1, quantity: 0 }] }
  })
  t.equal(res.statusCode, 400)
})

test('POST / returns 400 when item quantity is negative', async (t) => {
  const app = await build(t)

  const res = await app.inject({
    method: 'POST',
    url: '/',
    payload: { storeId: 'store-001', customerOrderId: 'order-abc-123', items: [{ productId: 1, quantity: -1 }] }
  })
  t.equal(res.statusCode, 400)
})

test('GET /health returns ok', async (t) => {
  const app = await build(t)

  const res = await app.inject({
    method: 'GET',
    url: '/health'
  })
  t.equal(res.statusCode, 200)
  t.same(JSON.parse(res.payload), { status: 'ok', version: '0.1.0' })
})

test('GET /hugs returns hugs', async (t) => {
  const app = await build(t)

  const res = await app.inject({
    method: 'GET',
    url: '/hugs'
  })
  t.equal(res.statusCode, 200)
  t.same(JSON.parse(res.payload), { hugs: 'hugs' })
})
