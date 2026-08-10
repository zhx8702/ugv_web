/**
 * Rosbridge composable – wraps roslibjs (ROSLIB) for direct
 * frontend ↔ ROS2 communication via WebSocket.
 *
 * Usage:
 *   const { rosConnected, connect, subscribe, publish } = useRosbridge()
 */
import { ref, shallowRef } from 'vue'
import * as ROSLIB_NPM from 'roslib'

// Resolve ROSLIB: prefer npm package, fallback to CDN global
const ROSLIB = ROSLIB_NPM?.default || ROSLIB_NPM || window.ROSLIB

// Module-level singleton so every component shares one connection
let ros = null
const rosConnected = ref(false)
let reconnectTimer = null

export function useRosbridge() {
  /**
   * Connect to rosbridge WebSocket.
   * @param {string} host - hostname (defaults to current page host)
   * @param {number} port - rosbridge port (default 5001)
   */
  function connect(host, port = 5001) {
    if (!ROSLIB) {
      console.warn('ROSLIB not loaded – install roslib via npm or include roslib.min.js in index.html')
      return
    }

    host = host || window.location.hostname

    if (ros && rosConnected.value) {
      return // already connected
    }

    ros = new ROSLIB.Ros({ url: `ws://${host}:${port}` })

    ros.on('connection', () => {
      rosConnected.value = true
      console.log('[rosbridge] connected')
      if (reconnectTimer) {
        clearInterval(reconnectTimer)
        reconnectTimer = null
      }
    })

    ros.on('close', () => {
      rosConnected.value = false
      console.log('[rosbridge] disconnected')
      // auto-reconnect
      if (!reconnectTimer) {
        reconnectTimer = setInterval(() => {
          if (!rosConnected.value) {
            try { ros.connect(`ws://${host}:${port}`) } catch { /* ignore */ }
          }
        }, 5000)
      }
    })

    ros.on('error', (err) => {
      console.error('[rosbridge] error:', err)
    })
  }

  function disconnect() {
    if (reconnectTimer) {
      clearInterval(reconnectTimer)
      reconnectTimer = null
    }
    if (ros) {
      try { ros.close() } catch { /* ignore */ }
      ros = null
    }
    rosConnected.value = false
  }

  /**
   * Subscribe to a ROS2 topic.
   * @returns {ROSLIB.Topic} the topic object (call .unsubscribe() to stop)
   */
  function subscribe(topicName, msgType, callback, throttleRate = 0) {
    if (!ros) return null
    const topic = new ROSLIB.Topic({
      ros,
      name: topicName,
      messageType: msgType,
      throttle_rate: throttleRate,
    })
    topic.subscribe(callback)
    return topic
  }

  /**
   * Publish a message to a ROS2 topic.
   */
  function publish(topicName, msgType, message) {
    if (!ros || !rosConnected.value) return
    const topic = new ROSLIB.Topic({
      ros,
      name: topicName,
      messageType: msgType,
    })
    topic.publish(new ROSLIB.Message(message))
  }

  /**
   * Call a ROS2 service.
   * @returns {Promise<object>}
   */
  function callService(serviceName, serviceType, request = {}) {
    return new Promise((resolve, reject) => {
      if (!ros) return reject(new Error('Not connected'))
      const service = new ROSLIB.Service({
        ros,
        name: serviceName,
        serviceType,
      })
      service.callService(
        new ROSLIB.ServiceRequest(request),
        (result) => resolve(result),
        (error) => reject(error)
      )
    })
  }

  return {
    rosConnected,
    connect,
    disconnect,
    subscribe,
    publish,
    callService,
  }
}
