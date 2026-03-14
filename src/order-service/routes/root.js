'use strict'

const orderSchema = {
  body: {
    type: 'object',
    required: ['storeId', 'customerOrderId', 'items'],
    properties: {
      storeId: { type: 'string' },
      customerOrderId: { type: 'string' },
      items: {
        type: 'array',
        minItems: 1,
        items: {
          type: 'object',
          required: ['productId', 'quantity'],
          properties: {
            productId: { type: 'integer' },
            quantity: { type: 'integer', minimum: 1 }
          }
        }
      }
    }
  }
}

module.exports = async function (fastify, opts) {
  fastify.post('/', { schema: orderSchema }, async function (request, reply) {
    const msg = request.body
    fastify.sendMessage(Buffer.from(JSON.stringify(msg)))
    reply.code(201)
  })

  fastify.get('/health', async function (request, reply) {
    const appVersion = process.env.APP_VERSION || '0.1.0'
    return { status: 'ok', version: appVersion }
  })

  fastify.get('/hugs', async function (request, reply) {
    return { hugs: fastify.someSupport() }
  })
}
