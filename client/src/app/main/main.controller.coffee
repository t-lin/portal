angular.module "throwdown"
  .controller "MainController", ($timeout, api, toastr) ->
    vm = this
    activate = ->
      $timeout (->
        vm.classAnimation = 'rubberBand'
        return
      ), 4000
      return

    showToastr = ->
      toastr.info 'Fork <a href="https://github.com/Swiip/generator-gulp-angular" target="_blank"><b>generator-gulp-angular</b></a>'
      vm.classAnimation = ''
      return

    getData = ->
      api.getServices().then (data) ->
        vm.services = data
      api.getVNets().then (data) ->
        vm.vnets = data

    vm.services = []
    vm.vnets = []
    vm.classAnimation = ''
    vm.creationDate = 1437624261595
    vm.showToastr = showToastr
    activate()
    getData()
    return
