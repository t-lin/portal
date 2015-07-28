angular.module "throwdown"
  .controller "MainController", ($timeout, $http) ->
    vm = this
    baseUrl = 'http://localhost:4040/api'
    endpointList = (endpoint) -> "#{baseUrl}/#{endpoint}"
    endpointId = (endpoint, id) -> "#{baseUrl}/#{endpoint}/#{id}"
    endpointIdVMs = (endpoint, id) -> "#{baseUrl}/#{endpoint}/#{id}/vms"
    activate = ->
      $timeout (->
        vm.classAnimation = 'rubberBand'
        return
      ), 4000
      getData()
      return

    showToastr = ->
      toastr.info 'Fork <a href="https://github.com/Swiip/generator-gulp-angular" target="_blank"><b>generator-gulp-angular</b></a>'
      vm.classAnimation = ''
      return

    getData = ->
      getPolicies().then (data) ->
        vm.policy = data[0]['network-policy']
        for dir in ['src_addresses', 'dst_addresses']
          vnet =  vm.policy['network_policy_entries']['policy_rule'][0][dir][0]
          console.log vnet
          getVNet(vnet.virtual_network).then do (dir=dir, id=vnet.virtual_network) ->
            (data) ->
              data.id = id
              vm.vnets[dir] = data
              console.log id, dir, data
              return
        service = vm.policy['network_policy_entries']['policy_rule'][0]['action_list']['apply_service'][0]
        console.log  service
        getServices(service).then (data) ->
          vm.service = data
          console.log data
        return
      return

    getPolicies = ->
      return $http.get(endpointList 'policies')
      .then(
        (response) -> response.data
        (response) -> []
      )
    getServices = (id) ->
      return $http.get(endpointId('services', id))
      .then(
        (response) -> response.data
        (response) -> []
      )
    getVNet = (id) ->
      return $http.get(endpointId('vnets', id))
      .then(
        (response) -> response.data
        (response) -> []
      )

    vm.service = ""
    vm.policy = ""
    vm.vnets = {}
    vm.classAnimation = ''
    vm.creationDate = 1437624261595
    vm.showToastr = showToastr
    activate()
    return
