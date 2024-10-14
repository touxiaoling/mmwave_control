#pragma once
#ifndef _FMC4030_DLL_H_
#define _FMC4030_DLL_H_

#ifdef FMC4030_DLL
#else
#define FMC4030_API  __declspec(dllexport) __stdcall
#endif

/* �������3�����������޸ģ���������ݴ��ҵ��³������ */
#define MAX_AXIS                     3

/* �豸״̬@machine_status.machineRunStatus */
#define MACHINE_MANUAL                     0x0001     //�豸�����ֶ�ģʽ
#define MACHINE_AUTO                       0x0002     //�豸�������нű�ģʽ

/* ����״̬@machine_status.axisStatus */                      
#define MACHINE_POWER_ON                   0x0000     //������
#define MACHINE_RUNNING                    0x0001     //����������
#define MACHINE_PAUSE                      0x0002     //����ͣ����
#define MACHINE_RESUME                     0x0004     //��
#define MACHINE_STOP                       0x0008     //��ֹͣ����
#define MACHINE_LIMIT_N                    0x0010     //����λ����
#define MACHINE_LIMIT_P                    0x0020	  //����λ����
#define MACHINE_HOME_DONE                  0x0040     //��������
#define MACHINE_HOME                       0x0080     //�������
#define MACHINE_AUTO_RUN                   0x0100     //��
#define MACHINE_LIMIT_N_NONE               0x0200     //����λδ����
#define MACHINE_LIMIT_P_NONE               0x0400     //����λδ����
#define MACHINE_HOME_NONE                  0x0800     //δ����
#define MACHINE_HOME_OVERTIME              0x1000     //���㳬ʱ

struct machine_status{
	float realPos[MAX_AXIS];
	float realSpeed[MAX_AXIS];
	unsigned int inputStatus;
	unsigned int outputStatus;
	unsigned int limitNStatus;
	unsigned int limitPStatus;
	unsigned int machineRunStatus;
	unsigned int axisStatus[MAX_AXIS];
	unsigned int homeStatus;
	char file[20][30];
};

struct machine_device_para{
	unsigned int id;
	unsigned int bound232;
	unsigned int bound485;
	char ip[15];
	int port;
	
	int div[MAX_AXIS];
	int lead[MAX_AXIS];
	int softLimitMax[MAX_AXIS];
	int softLimitMin[MAX_AXIS];
	int homeTime[MAX_AXIS];
};

struct machine_version{
	unsigned int firmware;
	unsigned int lib;
	unsigned int serialnumber;
};

#ifdef __cplusplus
extern "C" {
#endif

/* �豸����ر���غ��� */
int FMC4030_Open_Device(int id, char* ip, int port);
int FMC4030_Close_Device(int id);

/* �����˶�����״̬�����غ��� */
int FMC4030_Jog_Single_Axis(int id, int axis, float pos, float speed, float acc, float dec, int mode);
int FMC4030_Check_Axis_Is_Stop(int id, int axis);
int FMC4030_Home_Single_Axis(int id, int axis, float homeSpeed, float homeAccDec, float homeFallStep, int homeDir);
int FMC4030_Stop_Single_Axis(int id, int axis, int mode);
int FMC4030_Get_Axis_Current_Pos(int id, int axis, float* pos);
int FMC4030_Get_Axis_Current_Speed(int id, int axis, float* speed);

/* IO�������� */
int FMC4030_Set_Output(int id, int io, int status);
int FMC4030_Get_Input(int id, int io, int* status);

/* 485����ͨ�����ݲ������� */
int FMC4030_Write_Data_To_485(int id, char* send, int length);
int FMC4030_Read_Data_From_485(int id, char* recv, int* length);

/* 485������չ�豸�����������ڲ�����˾485��չ�豸�������������IO��չ����豸�� */
int FMC4030_Set_FSC_Speed(int id, int slaveId, float speed);

/* ModbusЭ�����������������FMC4030485���߷���ModbusЭ�����ݷ��ʴӻ��豸 */
/* 01�����룺��ȡ������Ȧֵ */
int FMC4030_MB01_Operation(int id, int slaveId, unsigned short int addr, char* recv, int* recvLength);

/* 03�����룺���Ĵ���ֵ */
int FMC4030_MB03_Operation(int id, int slaveId, unsigned short int addr, int numOfData, char* recv, int* recvLength);

/* 05�����룺д������Ȧֵ��1 �� 0 */
int FMC4030_MB05_Operation(int id, int slaveId, unsigned short int addr, unsigned short int val, char* recv, int* recvLength);

/* 06�����룺д�����Ĵ�����0x0000 ~ 0xFFFF */
int FMC4030_MB06_Operation(int id, int slaveId, unsigned short int addr, unsigned short int val, char* recv, int* recvLength);

/* 16�����룺д����Ĵ��� */
int FMC4030_MB16_Operation(int id, int slaveId, unsigned short int addr, int numOfData, unsigned short int* send, char* recv, int* recvLength);

/* ����岹��غ��� */
/** ���ܣ��Ե�ǰ��Ϊ��������ֱ�߲岹�˶�
  * id������
  * axis���岹����ţ�����ʮ�����Ƶĵ���λ��ʾX��Y��Z�ᣬ��ѡ����У�0x03��0x05��0x06��
  * endX���յ��X����ֵ
  * endY���յ��Y����ֵ
  * speed���岹�ٶȣ����ٶ�Ϊ����ϳ��ٶȣ����Ǹ�������ʵ�������ٶ�
  * acc���岹���ٶȣ��˼��ٶ�ͬ��Ϊ�ϳɼ��ٶ�
  * dcc���岹���ٶȣ��˼��ٶ�ͬ��Ϊ�ϳɼ��ٶ�
  */
int FMC4030_Line_2Axis(int id, unsigned int axis, float endX, float endY, float speed, float acc, float dec);

/** ���ܣ��Ե�ǰ��Ϊ��������ֱ�߲岹�˶�
  * id������
  * endX���յ��X����ֵ
  * endY���յ��Y����ֵ
  * endZ���յ��Z����ֵ
  * speed���岹�ٶȣ����ٶ�Ϊ����ϳ��ٶȣ����Ǹ�������ʵ�������ٶ�
  * acc���岹���ٶȣ��˼��ٶ�ͬ��Ϊ�ϳɼ��ٶ�
  * dcc���岹���ٶȣ��˼��ٶ�ͬ��Ϊ�ϳɼ��ٶ�
  */
int FMC4030_Line_3Axis(int id, unsigned int axis, float endX, float endY, float endZ, float speed, float acc, float dec);

/** ���ܣ��Ե�ǰ��Ϊ��������Բ���岹�˶�
  * id������
  * axis���岹����ţ�����ʮ�����Ƶĵ���λ��ʾX��Y��Z�ᣬ��ѡ����У�0x03��0x05��0x06��
  * endX���յ��X����ֵ
  * endY���յ��Y����ֵ
  * centerX��Բ��X����ֵ
  * centerY��Բ��Y����ֵ
  * radius��Բ�뾶
  * speed���岹�ٶȣ����ٶ�Ϊ����ϳ��ٶȣ����Ǹ�������ʵ�������ٶ�
  * acc���岹���ٶȣ��˼��ٶ�ͬ��Ϊ�ϳɼ��ٶ�
  * dcc���岹���ٶȣ��˼��ٶ�ͬ��Ϊ�ϳɼ��ٶ�
  */
int FMC4030_Arc_2Axis(int id, unsigned int axis, float endX, float endY, float centerX, float centerY, float radius, float speed, float acc, float dec, int dir);

int FMC4030_Pause_Run(int id, unsigned int axis);
int FMC4030_Resume_Run(int id, unsigned int axis);
int FMC4030_Stop_Run(int id);

/* �豸״̬��ѯ��غ��� */
/** ���ܣ���ѯ�豸״̬��Ϣ
  * id������
  * machineData��������ַ�����ָ�룬��machine_status����Ľṹ����ɣ�������ɺ����齫���������
  */
int FMC4030_Get_Machine_Status(int id, unsigned char* machineData);
int FMC4030_Get_Device_Para(int id, unsigned char* devicePara);
int FMC4030_Set_Device_Para(int id, unsigned char* devicePara);
int FMC4030_Get_Version_Info(int id, unsigned char* version);

/* �ļ�������غ��� */
/** ���ܣ����ؿ��ƿ������ļ���ű������ļ����ֱ�Ϊ.bin  .elo,�˺����������ļ��ϴ�ʱ�������ϳ�ʱ��
  * id������
  * filePath���ļ�·��
  * fileType���ļ�����  1�����ƿ����������ļ�  2�����ƿ��Զ�����ִ�нű��ļ�
  */
int FMC4030_Download_File(int id, char* filePath, int fileType);

/* �Զ�������غ��� */
/** ���ܣ��������ƿ��ڵĳ�������Զ�����
  * id������
  * file�����������ļ��������ļ����ӿ��ƿ��ڲ���ȡ
  */
int FMC4030_Start_Auto_Run(int id, char* file);

/** ���ܣ�ֹͣ���ƿ��Զ�����
  * id������
  */
int FMC4030_Stop_Auto_Run(int id);

/** ���ܣ�ɾ���������ڳ����ļ�
  * id������
  * file����ɾ�����ļ��������ļ����ӿ��ƿ��ڲ���ȡ
  */
int FMC4030_Delete_Script_File(int id, char* file);


#ifdef __cplusplus
}
#endif 

#endif