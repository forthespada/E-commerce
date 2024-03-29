------2022.01.23更新--------

鉴于自己的代码被人拿去获利，这违背了我的分享初衷，现全部清空个人以前分享的抓取代码



### 京东、苏宁、国美全站数据抓取

主要的数据包括**商品价格、名称、类别、描述**，以及**评论文本、评论时间、点赞数、评论人**等信息。

最终抓取**1000W**的商品URL，其中抓了大概**8000W**的商品数据和评论数据，后期数据量够了就没再做下去了。

**知乎**上有详细一点的介绍，如有需要请移步：https://zhuanlan.zhihu.com/p/146265932




#### 1、数据去重问题

全部的数据前期是采用**布隆过滤器**进行去重的，但后来发现并不需要这么麻烦，后用了一个小技巧进行去重。



因为每种商品是有一个大类的，比如手机里的苹果和水果里的苹果是不一样的，所以这两个苹果虽然一样，但是商品ID属于不一样的类别中的。借助这个小技巧进行URL的去重，自然这两个商品的信息价格包括评论都是不一样的了。同样的思想也被用在评论中，用这个小技巧做到了数据去重问题。



#### 2、网站介绍

##### **京东**

整体采用 IP代理池 + Seleium + MongoDB 做的，其中京东的商品价格做了二次隐藏，所以价格API接口需要自己用F12去查找，具体可以看一下JD的价格模块。

前期JD是没有反扒措施的，所以也比较友好，但是大概19年12月末就加上IP限制了，过快过多请求会直接封IP，没办法，后期只能上IP池了。

##### 苏宁、国美

这两个网站都相对友好一点，反扒没有那么严重，直接采用 Request + MySQL + MongoDB做的， 会用两个数据库是因为实验室总是断电，我又没有想到好的断电再续方式，只好先把全站商品URL保存下来，存到MySQL中去，然后再从MySQL中拿URL挨个抓取的。

只好用这种傻瓜式的方法了，哈哈~  



后面的时候，还借助JD的一个部分手机数据，使用[Neo4J图形数据库](https://baike.baidu.com/item/Neo4j/9952114?fr=aladdin)做了一个可视化的[小型手机知识图谱](https://github.com/forthespada/JD_Cellphone_KnowledgeGraph)

