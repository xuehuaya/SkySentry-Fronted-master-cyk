#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DJI WPML格式验证脚本
验证waylines.wpml文件是否符合DJI上云API要求的格式
"""

import xml.etree.ElementTree as ET
import sys
import os


class DJIWPMLValidator:
    def __init__(self):
        # DJI WPML命名空间
        self.namespaces = {
            'kml': 'http://www.opengis.net/kml/2.2',
            'wpml': 'http://www.dji.com/wpmz/1.0.2'
        }
        
        # 验证结果
        self.errors = []
        self.warnings = []
        self.info = []
        
    def validate_file(self, file_path: str) -> bool:
        """验证WPML文件"""
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                self.errors.append(f"文件不存在: {file_path}")
                return False
                
            # 解析XML文件
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            
            # 开始验证
            self.info.append(f"开始验证文件: {file_path}")
            
            # 验证根元素和命名空间
            self._validate_root_element(root)
            
            # 验证文档结构
            self._validate_document_structure(root)
            
            # 验证任务配置
            self._validate_mission_config(root)
            
            # 验证航线文件夹
            self._validate_folders(root)
            
            # 输出验证结果
            self._print_results()
            
            return len(self.errors) == 0
            
        except ET.ParseError as e:
            self.errors.append(f"XML解析错误: {e}")
            return False
        except Exception as e:
            self.errors.append(f"验证过程中发生错误: {e}")
            return False
    
    def _validate_root_element(self, root):
        """验证根元素和命名空间"""
        # 检查根元素是否为kml
        if root.tag != '{http://www.opengis.net/kml/2.2}kml':
            self.errors.append("根元素必须是kml，且使用正确的KML命名空间")
        else:
            self.info.append("✓ 根元素和KML命名空间正确")
        
    def _validate_document_structure(self, root):
        """验证文档结构"""
        # 查找Document元素
        document = root.find('kml:Document', self.namespaces)
        if document is None:
            self.errors.append("缺失Document元素")
            return
        else:
            self.info.append("✓ Document元素存在")
        
        return document
    
    def _validate_mission_config(self, root):
        """验证任务配置"""
        mission_config = root.find('.//wpml:missionConfig', self.namespaces)
        if mission_config is None:
            self.errors.append("缺失missionConfig元素")
            return
        
        self.info.append("✓ missionConfig元素存在")
        
        # 验证必要的配置项
        required_configs = [
            'flyToWaylineMode',
            'finishAction', 
            'exitOnRCLost',
            'executeRCLostAction',
            'takeOffSecurityHeight',
            'globalTransitionalSpeed'
        ]
        
        for config in required_configs:
            element = mission_config.find(f'wpml:{config}', self.namespaces)
            if element is None:
                self.warnings.append(f"建议添加配置项: {config}")
            else:
                self.info.append(f"✓ 配置项 {config}: {element.text}")
        
        # 验证无人机信息
        drone_info = mission_config.find('wpml:droneInfo', self.namespaces)
        if drone_info is not None:
            drone_enum = drone_info.find('wpml:droneEnumValue', self.namespaces)
            if drone_enum is not None:
                self.info.append(f"✓ 无人机型号代码: {drone_enum.text}")
        
        # 验证负载信息
        payload_info = mission_config.find('wpml:payloadInfo', self.namespaces)
        if payload_info is not None:
            payload_enum = payload_info.find('wpml:payloadEnumValue', self.namespaces)
            if payload_enum is not None:
                self.info.append(f"✓ 负载型号代码: {payload_enum.text}")
    
    def _validate_folders(self, root):
        """验证航线文件夹"""
        folders = root.findall('.//kml:Folder', self.namespaces)
        if not folders:
            self.errors.append("至少需要一个Folder元素来定义航线")
            return
        
        self.info.append(f"✓ 找到 {len(folders)} 个航线文件夹")
        
        for i, folder in enumerate(folders):
            self._validate_single_folder(folder, i)
    
    def _validate_single_folder(self, folder, folder_index):
        """验证单个航线文件夹"""
        self.info.append(f"\n--- 验证航线 {folder_index} ---")
        
        # 验证航线配置
        template_id = folder.find('wpml:templateId', self.namespaces)
        if template_id is not None:
            self.info.append(f"✓ 模板ID: {template_id.text}")
        
        wayline_id = folder.find('wpml:waylineId', self.namespaces)
        if wayline_id is not None:
            self.info.append(f"✓ 航线ID: {wayline_id.text}")
        
        execute_height_mode = folder.find('wpml:executeHeightMode', self.namespaces)
        if execute_height_mode is not None:
            self.info.append(f"✓ 高度模式: {execute_height_mode.text}")
        
        # 验证航点
        placemarks = folder.findall('kml:Placemark', self.namespaces)
        if not placemarks:
            self.errors.append(f"航线 {folder_index} 缺少航点(Placemark)")
            return
        
        self.info.append(f"✓ 航线 {folder_index} 包含 {len(placemarks)} 个航点")
        
        for j, placemark in enumerate(placemarks):
            self._validate_waypoint(placemark, folder_index, j)
    
    def _validate_waypoint(self, placemark, folder_index, waypoint_index):
        """验证单个航点"""
        # 验证坐标
        point = placemark.find('kml:Point/kml:coordinates', self.namespaces)
        if point is None:
            self.errors.append(f"航线 {folder_index} 航点 {waypoint_index} 缺少坐标信息")
        else:
            coords = point.text.strip()
            if self._validate_coordinates(coords):
                self.info.append(f"  ✓ 航点 {waypoint_index} 坐标: {coords}")
            else:
                self.errors.append(f"航线 {folder_index} 航点 {waypoint_index} 坐标格式错误: {coords}")
        
        # 验证航点索引
        index = placemark.find('wpml:index', self.namespaces)
        if index is None:
            self.errors.append(f"航线 {folder_index} 航点 {waypoint_index} 缺少index")
        else:
            try:
                idx_value = int(index.text)
                if idx_value != waypoint_index:
                    self.warnings.append(f"航点索引不连续: 期望 {waypoint_index}, 实际 {idx_value}")
                self.info.append(f"  ✓ 航点索引: {idx_value}")
            except ValueError:
                self.errors.append(f"航点索引格式错误: {index.text}")
        
        # 验证飞行高度
        execute_height = placemark.find('wpml:executeHeight', self.namespaces)
        if execute_height is None:
            self.warnings.append(f"航点 {waypoint_index} 缺少executeHeight")
        else:
            try:
                height = float(execute_height.text)
                self.info.append(f"  ✓ 飞行高度: {height}m")
            except ValueError:
                self.errors.append(f"飞行高度格式错误: {execute_height.text}")
        
        # 验证航点速度
        waypoint_speed = placemark.find('wpml:waypointSpeed', self.namespaces)
        if waypoint_speed is not None:
            try:
                speed = float(waypoint_speed.text)
                self.info.append(f"  ✓ 航点速度: {speed}m/s")
            except ValueError:
                self.errors.append(f"航点速度格式错误: {waypoint_speed.text}")
        
        # 验证航向参数
        heading_param = placemark.find('wpml:waypointHeadingParam', self.namespaces)
        if heading_param is not None:
            heading_mode = heading_param.find('wpml:waypointHeadingMode', self.namespaces)
            if heading_mode is not None:
                self.info.append(f"  ✓ 航向模式: {heading_mode.text}")
        
        # 验证转弯参数
        turn_param = placemark.find('wpml:waypointTurnParam', self.namespaces)
        if turn_param is not None:
            turn_mode = turn_param.find('wpml:waypointTurnMode', self.namespaces)
            if turn_mode is not None:
                self.info.append(f"  ✓ 转弯模式: {turn_mode.text}")
        
        # 验证动作组
        action_groups = placemark.findall('wpml:actionGroup', self.namespaces)
        if action_groups:
            self.info.append(f"  ✓ 航点 {waypoint_index} 包含 {len(action_groups)} 个动作组")
            for k, action_group in enumerate(action_groups):
                self._validate_action_group(action_group, folder_index, waypoint_index, k)
    
    def _validate_action_group(self, action_group, folder_index, waypoint_index, group_index):
        """验证动作组"""
        actions = action_group.findall('wpml:action', self.namespaces)
        if actions:
            self.info.append(f"    ✓ 动作组 {group_index} 包含 {len(actions)} 个动作")
            
            for action in actions:
                action_func = action.find('wpml:actionActuatorFunc', self.namespaces)
                if action_func is not None:
                    self.info.append(f"      - 动作类型: {action_func.text}")
    
    def _validate_coordinates(self, coords_text: str) -> bool:
        """验证坐标格式"""
        try:
            coords = coords_text.strip().split(',')
            if len(coords) < 2:
                return False
            
            lon = float(coords[0])
            lat = float(coords[1])
            
            # 检查经纬度范围
            if not (-180 <= lon <= 180):
                return False
            if not (-90 <= lat <= 90):
                return False
            
            return True
        except:
            return False
    
    def _print_results(self):
        """输出验证结果"""
        print("\n" + "="*60)
        print("DJI WPML文件验证结果")
        print("="*60)
        
        if self.errors:
            print(f"\n❌ 错误 ({len(self.errors)} 个):")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print(f"\n⚠️  警告 ({len(self.warnings)} 个):")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if self.info:
            print(f"\n📋 信息 ({len(self.info)} 个):")
            for info in self.info:
                print(f"  {info}")
        
        print("\n" + "="*60)
        if len(self.errors) == 0:
            print("✅ 验证通过！文件格式符合DJI WPML标准")
        else:
            print("❌ 验证失败！请修复上述错误")
        print("="*60)

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("使用方法: python validate_wpml.py <wpml文件路径>")
        print("示例: python validate_wpml.py waylines.wpml")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    validator = DJIWPMLValidator()
    is_valid = validator.validate_file(file_path)
    
    sys.exit(0 if is_valid else 1)

if __name__ == '__main__':
    main()