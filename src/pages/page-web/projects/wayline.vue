<template>
  <div class="project-wayline-wrapper height-100">
    <a-spin :spinning="loading" :delay="300" tip="downloading" size="large">
      <div style="height: 50px; line-height: 50px; border-bottom: 1px solid #4f4f4f; font-weight: 450;">
        <a-row>
          <a-col :span="1"></a-col>
          <a-col :span="15">Flight Route Library</a-col>
          <a-col :span="8" v-if="importVisible" class="flex-row flex-justify-end flex-align-center">
            <a-upload
              name="file"
              :multiple="false"
              accept=".kmz"
              :show-upload-list="false"
              :customRequest="uploadFile"
            >
              <a-button type="text" style="color: white;">
                <SelectOutlined />
              </a-button>
            </a-upload>
          </a-col>
        </a-row>
      </div>
      <div :style="{ height : height + 'px'}" class="scrollbar">
        <div id="data" class="height-100 uranus-scrollbar" v-if="waylinesData.data.length !== 0" @scroll="onScroll">
          <div v-for="wayline in waylinesData.data" :key="wayline.id">
            <div class="wayline-panel" style="padding-top: 5px;" @click="selectRoute(wayline)">
              <div class="title">
                <a-tooltip :title="wayline.name">
                  <div class="pr10" style="width: 120px; white-space: nowrap; text-overflow: ellipsis; overflow: hidden;">{{ wayline.name }}</div>
                </a-tooltip>
                <div class="ml10"><UserOutlined /></div>
                <a-tooltip :title="wayline.user_name">
                  <div class="ml5 pr10" style="width: 80px; white-space: nowrap; text-overflow: ellipsis; overflow: hidden;">{{ wayline.user_name }}</div>
                </a-tooltip>
                <div class="fz20 flex-row flex-align-center">
                  <a-tooltip title="Download KMZ">
                    <a-button type="text" size="small" style="color: white; margin-right: 5px;" @click.stop="downloadWayline(wayline.id, wayline.name)">
                      <DownloadOutlined />
                    </a-button>
                  </a-tooltip>
                  <a-dropdown>
                    <a style="color: white;">
                      <EllipsisOutlined />
                    </a>
                    <template #overlay>
                      <a-menu theme="dark" class="more" style="background: #3c3c3c;">
                        <a-menu-item @click="showWaylineTip(wayline.id)">
                          <span>Delete</span>
                        </a-menu-item>
                      </a-menu>
                    </template>
                  </a-dropdown>
                </div>
              </div>
              <div class="ml10 mt5" style="color: hsla(0,0%,100%,0.65);">
                <span><RocketOutlined /></span>
                <span class="ml5">{{ DEVICE_NAME[wayline.drone_model_key] }}</span>
                <span class="ml10"><CameraFilled style="border-top: 1px solid; padding-top: -3px;" /></span>
                <span class="ml5" v-for="payload in wayline.payload_model_keys" :key="payload.id">
                  {{ DEVICE_NAME[payload] }}
                </span>
              </div>
              <div class="mt5 ml10" style="color: hsla(0,0%,100%,0.35);">
                <span class="mr10">Update at {{ new Date(wayline.update_time).toLocaleString() }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-else>
          <a-empty :image-style="{ height: '60px', marginTop: '60px' }" />
        </div>
        <a-modal v-model:visible="deleteTip" width="450px" :closable="false" :maskClosable="false" centered :okButtonProps="{ danger: true }" @ok="deleteWayline">
          <p class="pt10 pl20" style="height: 50px;">Wayline file is unrecoverable once deleted. Continue?</p>
          <template #title>
            <div class="flex-row flex-justify-center">
              <span>Delete</span>
            </div>
          </template>
        </a-modal>
        <a-modal v-model:visible="previewVisible" title="doc.kml 内容预览" width="700px" :footer="null">
          <a-textarea v-model:value="previewContent" auto-size readonly style="font-family: monospace" />
        </a-modal>
      </div>
    </a-spin>
  </div>
</template>

<script lang="ts" setup>
import { reactive, ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import JSZip from 'jszip'
import { deleteWaylineFile, downloadWaylineFile, getWaylineFiles, importKmzFile } from '/@/api/wayline'
import { ELocalStorageKey, ERouterName } from '/@/types'
import { EllipsisOutlined, RocketOutlined, CameraFilled, UserOutlined, SelectOutlined, DownloadOutlined } from '@ant-design/icons-vue'
import { DEVICE_NAME } from '/@/types/device'
import { useMyStore } from '/@/store'
import { WaylineFile } from '/@/types/wayline'
import { downloadFile } from '/@/utils/common'
import { IPage } from '/@/api/http/type'
import { getRoot } from '/@/root'

const loading = ref(false)
const store = useMyStore()
const pagination: IPage = { page: 1, total: -1, page_size: 10 }
const waylinesData = reactive({ data: [] as WaylineFile[] })
const root = getRoot()
const workspaceId = localStorage.getItem(ELocalStorageKey.WorkspaceId)!
const deleteTip = ref(false)
const deleteWaylineId = ref('')
const canRefresh = ref(true)
const importVisible = ref(root.$router.currentRoute.value.name === ERouterName.WAYLINE)
const height = ref()

const previewVisible = ref(false)
const previewContent = ref('')

onMounted(() => {
  const parent = document.getElementsByClassName('scrollbar').item(0)?.parentNode as HTMLDivElement
  height.value = document.body.clientHeight - parent.firstElementChild!.clientHeight
  getWaylines()

  const key = setInterval(() => {
    const data = document.getElementById('data')?.lastElementChild as HTMLDivElement
    if (pagination.total === 0 || Math.ceil(pagination.total / pagination.page_size) <= pagination.page || height.value <= data?.clientHeight + data?.offsetTop) {
      clearInterval(key)
      return
    }
    pagination.page++
    getWaylines()
  }, 1000)
})

function getWaylines () {
  if (!canRefresh.value) return
  canRefresh.value = false
  getWaylineFiles(workspaceId, {
    page: pagination.page,
    page_size: pagination.page_size,
    order_by: 'update_time desc'
  }).then(res => {
    if (res.code !== 0) return
    waylinesData.data = [...waylinesData.data, ...res.data.list]
    pagination.total = res.data.pagination.total
    pagination.page = res.data.pagination.page
  }).finally(() => {
    canRefresh.value = true
  })
}

function showWaylineTip (id: string) {
  deleteWaylineId.value = id
  deleteTip.value = true
}

function deleteWayline () {
  deleteWaylineFile(workspaceId, deleteWaylineId.value).then(res => {
    if (res.code === 0) message.success('Wayline file deleted')
    deleteWaylineId.value = ''
    deleteTip.value = false
    pagination.total = 0
    pagination.page = 1
    waylinesData.data = []
    getWaylines()
  })
}

function downloadWayline (id: string, name: string) {
  loading.value = true
  downloadWaylineFile(workspaceId, id).then(res => {
    if (!res) return
    const blob = new Blob([res], { type: 'application/zip' })
    downloadFile(blob, name + '.kmz')
  }).finally(() => {
    loading.value = false
  })
}

function selectRoute (wayline: WaylineFile) {
  store.commit('SET_SELECT_WAYLINE_INFO', wayline)
}

function onScroll (e: any) {
  const el = e.srcElement
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 5 && Math.ceil(pagination.total / pagination.page_size) > pagination.page && canRefresh.value) {
    pagination.page++
    getWaylines()
  }
}

const uploadFile = async ({ file, onSuccess, onError }: any) => {
  loading.value = true
  try {
    const zip = await JSZip.loadAsync(file)
    const docKml = zip.file('doc.kml')
    if (!docKml) throw new Error('doc.kml not found in KMZ')

    const content = await docKml.async('string')
    previewContent.value = content
    previewVisible.value = true

    const formData = new FormData()
    formData.append('file', file)

    const res = await importKmzFile(workspaceId, formData)
    if (res.code === 0) {
      message.success(`${file.name} uploaded successfully`)
      canRefresh.value = true
      pagination.total = 0
      pagination.page = 1
      waylinesData.data = []
      getWaylines()
      onSuccess()
    } else {
      message.error(res.message || 'Upload failed')
      onError(new Error(res.message || 'Upload failed'))
    }
  } catch (err: any) {
    message.error('Upload error: ' + err.message)
    onError(err)
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.wayline-panel {
  background: #3c3c3c;
  margin-left: auto;
  margin-right: auto;
  margin-top: 10px;
  height: 90px;
  width: 95%;
  font-size: 13px;
  border-radius: 2px;
  cursor: pointer;
  .title {
    display: flex;
    flex-direction: row;
    align-items: center;
    height: 30px;
    font-weight: bold;
    margin: 0px 10px 0 10px;
  }
}
.uranus-scrollbar {
  overflow: auto;
  scrollbar-width: thin;
  scrollbar-color: #c5c8cc transparent;
}
</style>
