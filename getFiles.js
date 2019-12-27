const fs = require("fs");
const path = require("path");
const request = require("request");

const AUTHENTICATION = process.env.VIBE_CMS_TOKEN;
const MAINFILE = 'index.md';
const MAINID = process.env.MAIN_ID;
const CONFIGFOLDERNAME = 'option';

const deleteFolder= (path) => {
    let files = [];
    if( fs.existsSync(path) ) {
        files = fs.readdirSync(path);
        files.forEach(function(file,index){
            let curPath = path + "/" + file;
            if(fs.statSync(curPath).isDirectory()) {
                deleteFolder(curPath);
            } else {
                fs.unlinkSync(curPath);
            }
        });
        fs.rmdirSync(path);
    }
};

const options = (id) =>  {
    const api = {
        doc_id: id,
        export_format: {
            '.tag': 'markdown'
        }
    };
    return {
        url: 'https://api.dropboxapi.com/2/paper/docs/download',
        method: 'POST',
        headers: {
            'user-Agent': 'api-explorer-client',
            'authorization': AUTHENTICATION,
            'dropbox-API-Arg':  JSON.stringify(api)
        }
    }
};

const renameFolder = (str, fileName) => {
    const reg = /slug:.*?\n/;
    const slug = reg.exec(str);
    if (slug !== null) {
        const slugName = slug[0];
        let newFileName = slugName.replace('slug:', '');
        newFileName=newFileName.replace(/\ +/g,"");
        newFileName=newFileName.replace(/[\r\n]/g,"");

        deleteFolder(path.join(__dirname, 'content', 'blog', newFileName));
        fs.rename(path.join(__dirname, 'content', 'blog', fileName), path.join(__dirname, 'content', 'blog', newFileName),(error) => {
            error ? console.log('Rename failed', error) : console.log('Rename ok');
        });
    }
};

const cutMdFile = (fileName) => {
    const filePath = path.join(__dirname, 'content', 'blog', fileName, 'index.md');
    fs.readFile(filePath, function (err, data) {
        if (err) {
            throw Error(err);
        }
        let str = data.toString();
        const dirPath = path.join(__dirname, 'content', 'blog', fileName);
        let title = str.substring(0, str.indexOf('---'));
        title = title.replace('#', '');
        title = title.replace(/\ +/g,"");
        title = title.replace(/[\r\n]/g,"");

        str = str.substring(str.indexOf('---'), str.length);
        str = str.replace(/    ---/g, '---');
        str = str.replace(/    slug:/g, 'slug:');
        str = str.replace(/    date:/g, 'date:');
        str = str.replace(/    tags:/g, 'tags:');
        str = str.replace(/    draft:/g, 'draft:');
        // \[\+.*?\]
        str =  str.replace(/slug:(.+?)\n/g,res=>{
            return  `title: ${title}` + '\n' + res
        });
        let i = 0;
        str =  str.replace(/http[s]?:\/\/.+\.(jpg|jpeg|png)/g,res=>{
            if(res.indexOf('.jpeg')) {
                res.replace(/.jpeg/g, '.jpg');
            }
            i++;
            const imgName = (i === 1 ? 'cover' : i) + '.' + res.split('.').pop();
            createFolder(dirPath, {url: res}, false, imgName);
            return imgName
        });
        fs.writeFile(filePath, str,(err)=>{
            if (err) {
                throw Error(err);
            }
            renameFolder(str, fileName);
        });
    });
};

const getAllFile = () => {
    fs.readFile(path.join(__dirname, CONFIGFOLDERNAME, MAINFILE), function (err, data) {
        if (err) {
            throw Error(err);
        }
        const str = data.toString();

        str.split('\n').forEach(u => {
            let file_name = '';
            u.replace(/\[\+.*?\]/g,res=>{
                let newStr = res.replace(/\[\+/g, '');
                newStr = newStr.replace(/\]/g, '');
                file_name = newStr
            });

            if (file_name !== '') {
                if(file_name.indexOf('/') !== -1) {
                    file_name = file_name.substring(file_name.lastIndexOf('/') + 1, file_name.length);
                    file_name = file_name.substring(file_name.indexOf(' ') + 1, file_name.length);
                    console.log('Tip: don\'t put symbols in the title / ')
                }
                const doc_id = u.substring(u.length - MAINID.length - 2, u.length - 2);
                createFolder(path.join(__dirname, 'content', 'blog', file_name), options(doc_id), () => cutMdFile(file_name))
            }
        })
    });
};

const createFolder = (dirPath, options, event, fileName) => {
    if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath);
        console.log("Folder created successfully");
    } else {
        console.log(`Folder already exists：${dirPath}`);
    }

    const writeStream = fs.createWriteStream(path.join(dirPath, fileName || MAINFILE));
    const readStream = request(options);
    readStream.pipe(writeStream);
    readStream.on('end', function() {
        console.log('Download successful！');
    });
    readStream.on('error', function(err) {
        throw Error(err);
    });
    writeStream.on("finish", function() {
        console.log("Write successfully！");
        writeStream.end();
        event && event()
    });
};

try{
    createFolder(path.join(__dirname, CONFIGFOLDERNAME), options(MAINID), getAllFile);
}catch (e) {
    console.log(e)
}