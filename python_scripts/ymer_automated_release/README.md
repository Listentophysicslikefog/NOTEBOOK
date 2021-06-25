# ymer模块自动化变更
变更一般在周一 到 周四进行；  
变更的region必须和管理机名字一一对应，同一个管理机同时只可以有一个在变更ymer，代码已经保证该要求，如果没有一一对应会停止变更； 

# 1. 自动化变更适用范围及要求 

1. 变更的region必须和管理机一一对应，同一个管理机同时只可以变更一个模块，即相同管理机器上面已经有其他模块(如： chunk )在变更，那么ymer模块需要等待其他模块变更完成后再变更

2. 该模块只适用clone模块ymer的变更

3. limax/udisk/tool/release/ymer_automated_release 目录下所有的模块均为ymer clone 自动化变更模块独立所有不可随意改动

# 2. 自动化变更功能 及 变更时的风险点避免

## 2.1 变更时的风险点避免


1. ymer自动化变更模块依赖的host_ip以及配置均与其它模块变更独立开。 所以其他模块即使和ymer模块在同一个管理机同时变更，ymer变更不会影响其它任何模块的变更同时ymer变更也不受任何模块变更的影响，尽可能避免变更时配置被覆盖的风险

2. 在变更前会对环境进行检测，当变更的区域region和管理机名字不对应时会停止变更

3. 在变更前检测当前管理机/root/ymer_deploy_lock目录下是否有锁，如果有停止变更，如果没有则添加锁

4. ymer自动化变更保正，发布的管理机器与需要变更的区域一致避免不同的管理机器同时变更同一个region、一个管理机同时只可以有一个ymer在进行自动化变更


## 2.2 自动化变更的功能

1. 变更region、set可配置，串行依次变更多个set或者整个机房

2. 变更的类型可以配置：non-p2p（只变更非p2p的set）、p2p(只变更p2p的set)、all(变更所有set) 

3. 每个set的属性（p2p和非p2p）自动化判断，并且可以根据配置自动变更对应的set

4. 变更日志存放到指定文件夹(ymer_deploy_log)持久化以及前台输出

5. 每次变更的前set的相关配置以及二进制文件均会备份

6. 变更前会先关闭当前需要变更的set，变更验证完成后会恢复当前变更set之前的状态 

7. 变更完成一个set后会对该set进行clone验证并且获取该盘的状态，进一步判断是否变更成功，不需要手动验证

8. 验证完成后删除验证时创建的盘，并且恢复该set之前状态然后进行下一个set的变更

9. 变更失败后通过电话告警通知变更人

# 3. 使用方法

## 3.1 先配置release_lists.json文件

{
    "release_info" :[

        {

         "region":"hn02" ,            // 需要变更的region

         "set":[3101,1100] ,          // 需要变更的set，当release_one_region配置为No时才有效

         "release_type" : "all",      // 需要变更的set类型：p2p、non-p2p、all

         "release_one_region" : "No", // 是否需要变更整个region的set

         "clone_image" : "bsi-o1y4hh",// 验证变更时clone的镜像源，不同的区域需要不同的镜像源

         "image_size": 20             // 镜像源大小

        }

    ],

    "version"        :"21.03.12-6cc73fd-centos7-x86_64", // 需要变更的版本

    "deploy_center"  :"172.20.180.156",
}

## 3.2 开始变更

可以在前台直接看到输出的变更日志或者到ymer_deploy_log文件夹下看对应的变更日志

python  ymer_auto_release_start.py



