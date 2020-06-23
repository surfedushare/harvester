import * as Sentry from '@sentry/browser'
import * as Integrations from '@sentry/integrations'

if (process.env.VUE_APP_USE_SENTRY) {
  Sentry.init({
    dsn: 'https://21fab3e788584cbe999f20ea1bb7e2df@sentry.io/2964956',
    integrations: [new Integrations.CaptureConsole()],
    beforeSend(event) {
      if (event.user) {
        delete event.user
      }
      if (
        event.request &&
        event.request.headers &&
        event.request.headers['User-Agent']
      ) {
        delete event.request.headers['User-Agent']
      }
      return event
    }
  })
}

import Vue from 'vue'
import injector from 'vue-inject'
import { createApp } from './index'
import { getMatchedComponents, setContext } from './utils'
import '@fortawesome/fontawesome-free/css/all.css'
import router from '~/router'

// Global shared references
let app
const $log = injector.get('$log')

Object.assign(Vue.config, { silent: true, performance: false })

// Create and mount App
createApp()
  .then(mountApp)
  .catch(err => {
    $log.error('[nuxt] Error while initializing app', err)
  })

async function render(to, from, next) {
  // nextCalled is true when redirected
  let nextCalled = false
  const _next = path => {
    if (from.path === path.path && this.$loading.finish) {
      this.$loading.finish()
    }

    if (from.path !== path.path && this.$loading.pause) {
      this.$loading.pause()
    }

    if (nextCalled) return
    nextCalled = true
    next(path)
  }

  // Update context
  await setContext(app, {
    route: to,
    from,
    next: _next.bind(this)
  })

  // Get route's matched components
  const matches = []
  const Components = getMatchedComponents(to, matches)

  // Update ._data and other properties if hot reloaded
  Components.forEach(Component => {
    if (Component._Ctor && Component._Ctor.options) {
      Component.options.asyncData = Component._Ctor.options.asyncData
      Component.options.fetch = Component._Ctor.options.fetch
    }
  })

  // If not redirected
  if (!nextCalled) {
    if (this.$loading.finish && !this.$loading.manual) {
      this.$loading.finish()
    }

    next()
  }
}

async function mountApp(__app) {
  // Set global variables
  app = __app.app

  // Create Vue instance
  const _app = new Vue({
    ...app,
    router,
    app
  })

  // Mounts Vue app to DOM element
  const mount = () => {
    _app.$mount('#__nuxt')
  }

  // Initialize error handler
  _app.$loading = {} // To avoid error while _app.$nuxt does not exist

  // Add router hooks
  router.beforeEach(render.bind(_app))
  router.afterEach(to => {
    // Parse URL and set filters selected when
    let filters = _app.$store.getters.getFiltersFromQuery(to.query)
    _app.$store.commit('SETUP_FILTER_CATEGORIES', filters)
  })

  mount()
}
