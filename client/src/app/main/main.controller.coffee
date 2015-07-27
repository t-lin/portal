angular.module "throwdown"
  .controller "MainController", ($timeout, api, toastr) ->
    vm = this
    activate = ->
      $timeout (->
        vm.classAnimation = 'rubberBand'
        return
      ), 4000
      getServices()
      return

    showToastr = ->
      toastr.info 'Fork <a href="https://github.com/Swiip/generator-gulp-angular" target="_blank"><b>generator-gulp-angular</b></a>'
      vm.classAnimation = ''
      return

    getServices = ->
      api.getServices().then (data) ->
        console.log data
        vm.services = data

    vm.services = []

    vm.classAnimation = ''
    vm.creationDate = 1437624261595
    vm.showToastr = showToastr
    activate()
    return
